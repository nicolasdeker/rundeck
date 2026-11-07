# `rdx-nodes`

node model, node filter language, resource model sources, caching, node enhancers

Nodes: the node entry model, the node filter language (`name:`, `tags:`, attribute filters, regex, exclusion),
resource model sources (file, url, script, directory, built-in), caching and node enhancers. The filter parser
gets property tests and a fuzz target.

## Legacy references (ported in later phases)

- `legacy/core/src/main/java/com/dtolabs/rundeck/core/utils/NodeSet.java`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/common/NodeFilter.java`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/common/NodeSetImpl.java`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/resources/` (model sources)
- `legacy/rundeckapp/grails-app/services/rundeck/services/NodeService.groovy`
- `legacy/rundeckapp/grails-app/services/rundeck/services/nodes/`
- `legacy/plugins/source-refresh-plugin/`

## Parity specs this crate targets

- `specs/nodes.md`, `specs/node-filter.md`
- upstream `api/nodes/NodesSpec`, `api/resourceModel/AnsibleResourceModelSpec`

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
