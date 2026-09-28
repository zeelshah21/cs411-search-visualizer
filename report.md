# Project 1 Report: Intelligent Search Visualizer

> [!IMPORTANT]
> **AUTOGRADER COMPLIANCE INSTRUCTIONS:**
> This report is parsed automatically by the autograder. To ensure you receive full credit for your work:
> 1. **Do not modify** the section headers (`## ...`) or bold field keys (e.g., `**Name:**`, `**Selected Region:**`, `**Live Deployment URL:**`, etc.).
> 2. **Write your answers directly after** the colon `:` of each field, replacing the placeholder text completely (including the outer brackets `[` and `]`).
> 3. **Maintain the file structure**. Changing headers, bold titles, or deleting lines can cause the autograder to miss your responses and award 0 marks.

---

## Student Information 
- **Name:** Zeel Shah
- **UID (netID):** zshah27
- **UIN:** [Write your UIN here]

---

## Section 1: Selected City Region
- **Selected Region:** Illinois, USA (statewide road network, from Galena and Waukegan in the north down to Carbondale in the south)

---

## Section 2: Map Graph Configuration
- **Total Cities Configured:** 25
- **Total Connection Edges:** 42
- **Graph Fully Connected:** Yes

---

## Section 3: Local Verification & Search Algorithms
*Check the algorithms you successfully ran and verified on your local development server by placing an `x` in the brackets (e.g., `[x]`):*
- [x] Breadth-First Search (BFS)
- [x] Depth-First Search (DFS)
- [x] Uniform Cost Search (UCS)
- [x] Iterative Deepening Search (IDS)
- [x] Greedy Best-First Search (Greedy)
- [x] A* Search (A*)

---

## Section 4: Deployed and Presentation Information
- **Deployment Platform:** Render
- **Live Deployment URL:** [Provide your live deployment site URL here]
- **Video Presentation Link:** [Provide an accessible link to your 5–7 minute video presentation]

---

## Section 5: Discussion
- **Which search algorithm is best for this route finding problem?** 
    A* is the best choice for this problem. It always returns the shortest road distance (same answer as UCS) but expands fewer cities, because the straight-line (haversine) heuristic steers it toward the destination. Straight-line distance can never be longer than the real driving distance, so the heuristic is admissible and consistent, which guarantees A* is optimal here. UCS is also optimal but searches in every direction, so it wastes work on cities behind the start. BFS and IDS only minimize the number of stops, not the miles, and DFS and Greedy can return noticeably longer routes.
- **Search Efficiency (Nodes expanded/time taken comparison):** Using the "Compare all" button (for example Chicago to Carbondale), IDS expanded by far the most nodes, since it re-runs depth-limited DFS from scratch for every depth limit and re-expands the shallow cities each time. UCS expanded close to every city in the graph because it grows outward by path cost in all directions. BFS expanded a lot as well, while A* expanded noticeably fewer than UCS for the same optimal cost. Greedy expanded the fewest nodes because it heads straight at the goal, but it does not guarantee the shortest route, and on some pairs it returns a longer one. DFS's node count depends a lot on neighbor ordering and it often returned the longest, most roundabout path. With only 25 cities every algorithm ran in well under a millisecond, so runtime differences are tiny. Nodes expanded is the more meaningful comparison, and on a much bigger map the gap between A* and UCS/BFS/IDS would grow a lot.
- **Link the idea of search algorithm to today Generative AI.** 
    Generative AI models like LLMs are also doing a kind of search. At each step the model has a huge space of possible next tokens (the "actions") and a score for each one (like a cost or heuristic). Greedy decoding is basically greedy best-first search: always take the token that looks best right now, which is fast but can lead to a worse overall answer. Beam search keeps the top k partial sequences, like a memory-bounded best-first search. Newer reasoning models go further and explore multiple reasoning paths, score them with a learned value or reward model (similar to a heuristic h(n)), and backtrack from bad ones, which is close to tree search methods like A* or Monte Carlo Tree Search. Agents that plan tool calls or routes also search over a state space, with the LLM acting as the heuristic that guesses which step gets closer to the goal. So the same trade-offs from this project apply: better heuristics mean less exploration, and greedy choices are fast but not guaranteed optimal.

