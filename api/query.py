import graphene
import re
from ens.utils import label_to_hash, name_to_hash, normalize_name
from hexbytes import HexBytes


node_re = re.compile("^0x[0-9a-zA-Z]{64}$")
ROOT_NODE = '0x0000000000000000000000000000000000000000000000000000000000000000'

class EventFields(graphene.AbstractType):
    blockNumber = graphene.Int(required=True)
    logIndex = graphene.Int(required=True)
    blockHash = graphene.String(required=True)
    transactionHash = graphene.String(required=True)


class ResolverEvent(graphene.Interface, EventFields):
    resolver = graphene.Field(lambda:Resolver, required=True)


class AddrEvent(graphene.ObjectType):
    class Meta:
        interfaces = (ResolverEvent,)

    a = graphene.Field(lambda:Address)


class RegistryEvent(graphene.Interface, EventFields):
    domain = graphene.Field(lambda:Domain, required=True)


class SubdomainTransferEvent(graphene.ObjectType):
    class Meta:
        interfaces = (RegistryEvent,)

    labelhash = graphene.String(required=True)
    label = graphene.String()
    subdomain = graphene.Field(lambda:Domain)
    owner = graphene.Field(lambda:Address, required=True)

    async def resolve_label(self, info):
        if self.label is None:
            self.label = await info.context['backend'].get_preimage.load(self.labelhash)
        return self.label


class TransferEvent(graphene.ObjectType):
    class Meta:
        interfaces = (RegistryEvent,)

    owner = graphene.Field(lambda:Address, required=True)


class NewResolverEvent(graphene.ObjectType):
    class Meta:
        interfaces = (RegistryEvent,)

    resolver = graphene.Field(lambda:Resolver, required=True)


class NewTTLEvent(graphene.ObjectType):
    class Meta:
        interfaces = (RegistryEvent,)

    ttl = graphene.Int(required=True)


class DomainConnection(graphene.ObjectType):
    domains = graphene.List(lambda:Domain)
    next = graphene.String()


class Address(graphene.ObjectType):
    address = graphene.String(required=True)
    ownedNames = graphene.Field(DomainConnection, limit=graphene.Int(), start=graphene.String())

    async def resolve_ownedNames(self, info, limit=None, start=None):
        domains = [Domain(namehash=namehash) for namehash in await info.context['backend'].get_owned_names(self.address, limit=limit, start=start)]
        cursor = None
        if len(domains) > 0 and (limit is None or limit == len(domains)):
            cursor = domains[-1].namehash + '00'
        return DomainConnection(domains=domains, next=cursor)


class ResolverEventConnection(graphene.ObjectType):
    events = graphene.List(ResolverEvent)
    next = graphene.String()


class Resolver(graphene.ObjectType):
    address = graphene.Field(Address, required=True)
    domain = graphene.Field(lambda:Domain, required=True)
    history = graphene.Field(ResolverEventConnection, limit=graphene.Int(), start=graphene.String())

    async def resolve_history(self, info, limit=None, start=None):
        events = []
        if start is not None:
            start = tuple(int(x) for x in start.split(':'[1]))
        for event in await info.context['backend'].get_resolver_events(self.address.address, self.domain.namehash, limit=limit, start=start):
            fields = {k: event[k] for k in ['blockNumber', 'blockHash', 'transactionHash', 'logIndex']}
            if 'a' in event:
                events.append(AddrEvent(resolver=self, a=Address(address=event['a']), **fields))
        cursor = None
        if len(events) > 0 and (limit is None or limit == len(events)):
            cursor = "%s:%s" % (events[-1].blockNumber, int(events[-1].logIndex) - 1)
        return ResolverEventConnection(events=events, next=cursor)


class RegistryEventConnection(graphene.ObjectType):
    events = graphene.List(RegistryEvent)
    next = graphene.String()


class Domain(graphene.ObjectType):
    namehash = graphene.String(required=True)
    name = graphene.String()
    labelhash = graphene.String()
    label = graphene.String()
    parent = graphene.Field(lambda:Domain)
    labels = graphene.List(graphene.String)
    subdomains = graphene.Field(DomainConnection, limit=graphene.Int(), start=graphene.String())
    owner = graphene.Field(Address)
    resolver = graphene.Field(Resolver)
    ttl = graphene.Int()
    history = graphene.Field(RegistryEventConnection, limit=graphene.Int(), start=graphene.String())

    async def resolve_name(self, info):
        if self.name is None:
            labels = await self.resolve_labels(info)
            self.name = '.'.join(labels)
        return self.name

    async def _fetch_parent(self, backend):
        node, label = await backend.get_parent_name.load(self.namehash)
        if self.name is not None:
            if '.' in self.name:
                self.parent = Domain(namehash=node, name=self.name.split('.', 1)[1])
            else:
                self.parent = Domain(namehash=node, name='')
        else:
            self.parent = Domain(namehash=node)
        self.labelhash = label

    async def resolve_labelhash(self, info):
        if self.namehash == ROOT_NODE:
            return None
        if self.name is not None:
            return label_to_hash(self.name.split('.', 1)[0]).hex()
        if self.labelhash is None:
            await self._fetch_parent(info.context['backend'])
        return self.labelhash

    async def resolve_label(self, info):
        if self.namehash == ROOT_NODE:
            return None
        if self.name is not None:
            return self.name.split('.', 1)[0]
        if self.label is None:
            self.label = await info.context['backend'].get_preimage.load(await self.resolve_labelhash(info))
        return self.label

    async def resolve_parent(self, info):
        if self.namehash == ROOT_NODE:
            return None
        if self.name is not None:
            if '.' in self.name:
                parentName = self.name.split('.', 1)[1]
                return Domain(name=parentName, namehash=name_to_hash(parentName).hex())
            else:
                return Domain(name='', namehash=ROOT_NODE)
        if self.parent is None:
            await self._fetch_parent(info.context['backend'])
        return self.parent

    async def resolve_labels(self, info):
        if self.namehash == ROOT_NODE:
            return []
        if self.name is not None:
            return self.name.split('.')
        if self.labels is None:
            self.labels = [await self.resolve_label(info)] + await (await self.resolve_parent(info)).resolve_labels(info)
        return self.labels

    async def resolve_subdomains(self, info, limit=None, start=None):
        domains = [Domain(labelhash=x[0], namehash=x[1], parent=self) for x in await info.context['backend'].get_subdomains(self.namehash, limit=limit, start=start)]
        cursor = None
        if len(domains) > 0 and (limit is None or limit == len(domains)):
            cursor = domains[-1].labelhash + '00'
        return DomainConnection(domains=domains, next=cursor)

    async def _query_registry(self, backend):
        result = await backend.query_registry.load(self.namehash)
        self.owner = Address(address=result.get('owner'))
        self.resolver = Resolver(address=Address(address=result.get('resolver')), domain=self)
        self.ttl = result.get('ttl')
        self.label = result.get('label')

    async def resolve_owner(self, info):
        if self.owner is None:
            await self._query_registry(info.context['backend'])
        return self.owner

    async def resolve_resolver(self, info):
        if self.resolver is None:
            await self._query_registry(info.context['backend'])
        return self.resolver

    async def resolve_ttl(self, info):
        if self.ttl is None:
            await self._query_registry(info.context['backend'])
        return self.ttl

    async def resolve_history(self, info, limit=None, start=None):
        events = []
        if start is not None:
            start = tuple(int(x) for x in start.split(":", 1))
        for event in await info.context['backend'].get_registry_events(self.namehash, limit=limit, start=start):
            fields = {k: event[k] for k in ['blockNumber', 'blockHash', 'transactionHash', 'logIndex']}
            if event['_eventName'] == 'NewOwner':
                events.append(SubdomainTransferEvent(domain=self, labelhash=event['label'], owner=Address(address=event['owner']), **fields))
            elif event['_eventName'] == 'Transfer':
                events.append(TransferEvent(domain=self, owner=Address(address=event['owner']), **fields))
            elif event['_eventName'] == 'NewResolver':
                events.append(NewResolverEvent(domain=self, resolver=Resolver(address=Address(address=event['resolver']), domain=self), **fields))
            elif event['_eventName'] == 'NewTTL':
                events.append(NewTTLEvent(domain=self, ttl=event['ttl'], **fields))
        cursor = None
        if len(events) > 0 and (limit is None or limit == len(events)):
            cursor = "%s:%s" % (events[-1].blockNumber, int(events[-1].logIndex) - 1)
        return RegistryEventConnection(events=events, next=cursor)


class Query(graphene.ObjectType):
    domain = graphene.Field(Domain, name=graphene.String(required=True))
    address = graphene.Field(Address, address=graphene.String(required=True))

    def resolve_domain(self, info, name):
        if node_re.match(name):
            return Domain(namehash=name)
        return Domain(name=name, namehash=name_to_hash(name).hex())


    def resolve_address(self, info, address):
        return Address(address)


schema = graphene.Schema(query=Query, types=[SubdomainTransferEvent, TransferEvent, NewResolverEvent, NewTTLEvent, AddrEvent])
