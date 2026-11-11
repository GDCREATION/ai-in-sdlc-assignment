---
name: cited-diagrams
description: Draws as-built and target architecture diagrams in Mermaid where every node and arrow cites a file or symbol, inferred items are listed separately, and anything not in the code is marked absent. Use when producing container diagrams, sequence diagrams, C4 views, or architecture docs for this repository.
---

# Cited diagrams

## Rules

1. Read the code before drawing. Prefer a file path and a type or method name over a description.
2. Every node and every arrow in the Mermaid source has a matching entry in a citation list. The citation is a file path or a symbol that exists in the repo.
3. Put anything you concluded without a direct read in a separate list headed "Inferred". Do not leave inferred items inside the citation list.
4. As-built diagrams contain only containers and calls that exist in the code. Azure SQL, Azure Service Bus, and PayEx are not in the code. If a target diagram includes them, label each one "not in the code yet" and give it no arrow that pretends the call exists.
5. `ops/` is the planned deployment. It is not a citation for current behavior.
6. Keep the browser, the API host, the domain library, and the in-memory store distinct. In-process calls are not network hops; say so in the inferred list when the diagram splits them into participants.
7. After drafting, open each cited file and correct any node, arrow, or status that the file does not support.

## Output

- Mermaid source for the container view and the sequence.
- Citation list, one line per element id.
- Inferred list, which may be empty only after an explicit check.
- The command that renders or validates the diagrams, when one was run.
