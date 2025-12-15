# 🦁 30 Wild Use Cases for Kirosu

A gradient of automation ideas, ranging from "Safe & Boring" (0/100) to "Skynet Risk" (100/100).

---

## 🟢 Level 1: The "Safe & Sane" (0-30/100)
*Everyday utilities that save time.*

1.  **The Typosquatting Fixer (5/100)**
    *   **Goal**: Check every file in a repo for common typos.
    *   **How**: `kirosu run-recursive "Find spelling errors in all .md files and create a PR"`

2.  **Jira Ticket Summarizer (10/100)**
    *   **Goal**: Read 50 open tickets and summarize the main blockers.
    *   **How**: `kirosu agent` with `jira-cli` tool.

3.  **Readme Polisher (12/100)**
    *   **Goal**: Keep `README.md` in sync with code changes.
    *   **How**: Run on git hook. `kirosu task add "Check if README matches src/"`

4.  **Log Noise Filter (15/100)**
    *   **Goal**: Analyze 10GB of logs, delete "INFO" noise, keep "ERROR".
    *   **How**: Swarm with `grep` capability working in parallel chunks.

5.  **Dependency Updater (20/100)**
    *   **Goal**: Check `pyproject.toml`, find outdated libs, run tests if updated.
    *   **How**: A simple "Maintenance Agent".

6.  **Unit Test Filler (25/100)**
    *   **Goal**: Find functions with 0% coverage and write basic tests.
    *   **How**: `kirosu agent` pointed at `tests/` dir.

7.  **CSS Class Cleaner (28/100)**
    *   **Goal**: Find unused CSS classes in a web project.
    *   **How**: Agent scans HTML vs CSS files.

8.  **Automated Translator (30/100)**
    *   **Goal**: Translate `locales/en.json` to 10 other languages.
    *   **How**: 10 Agents running in parallel, one per language.

---

## 🟡 Level 2: The "Power User" (31-70/100)
*Complex workflows effectively replacing a junior dev.*

9.  **The Refactor Swarm (35/100)**
    *   **Goal**: Convert an entire Python 2 codebase to Python 3.
    *   **How**: `kirosu run-recursive "Convert all files to Py3, run verify script"`

10. **Documentation Generator (40/100)**
    *   **Goal**: Read code, generate Sphinx docs, build site, deploy to Netlify.
    *   **How**: Pipeline: Reader -> Writer -> Deployer.

11. **Security Red Teamer (45/100)**
    *   **Goal**: Try to inject SQL into your own API endpoints.
    *   **How**: Agent with `curl` and a list of payloads targeting localhost.

12. **Stack Overflow Answerer (50/100)**
    *   **Goal**: Watch a tag, generate answer, draft it for human review.
    *   **How**: `kirosu` polling RSS feed + HITL (`kirosu approve`).

13. **Twitter/X Bot Farm (Legal) (55/100)**
    *   **Goal**: 5 agents each monitoring a coding niche (Rust, AI, Web) and curating news.
    *   **How**: Isolated workspaces, distinct personalities in `.kiro/context.md`.

14. **Integration Test Writer (60/100)**
    *   **Goal**: Spin up docker-compose, click buttons (via puppeteer), verify UI.
    *   **How**: Agent with `browser-use` or `playwright`.

15. **Data Scraper & Analyzer (65/100)**
    *   **Goal**: Scrape 1000 news sites, sentiment analyze, plot trend graph.
    *   **How**: Map-Reduce topology. 10 Scrapers -> 1 Aggregator.

16. **Code Review Sentinel (68/100)**
    *   **Goal**: Auto-comment on PRs with "Performance", "Security", and "Style" reviews.
    *   **How**: 3 Parallel agents triggered by GitHub Actions.

17. **Legacy Code Killer (70/100)**
    *   **Goal**: Identify dead functions via call graph analysis and delete them.
    *   **How**: "Dangerous Mode" enabled. Python static analysis tools.

---

## 🔴 Level 3: The "Mad Scientist" (71-90/100)
*Autonomous behaviors that might surprise you.*

18. **The "Auto-Fixer" Loop (75/100)**
    *   **Goal**: Run tests. If fail, fix code. Run tests. Repeat until pass.
    *   **How**: `kirosu agent` in a `while ! pytest` loop.

19. **Library Migration Swarm (80/100)**
    *   **Goal**: Swap `requests` for `httpx` across 500 files, updating async syntax.
    *   **How**: Massive parallel swarm with `codex` provider.

20. **Chaos Monkey Agent (82/100)**
    *   **Goal**: Randomly kill docker containers or delete db rows to test resilience.
    *   **How**: Agent with `docker` socket access and RNG.

21. **The "Interviewer" (85/100)**
    *   **Goal**: Conduct a technical interview with a human via chat.
    *   **How**: Agent instructed to ask progressively harder questions based on answers.

22. **Competitive Programmer (88/100)**
    *   **Goal**: Solve Project Euler problems 1-100 automatically.
    *   **How**: Agent reads problem -> Writes Code -> Submits -> Retries.

23. **Self-Documentation (90/100)**
    *   **Goal**: Kirosu reads its own source code and updates its own `technology.md`.
    *   **How**: Point `kirosu` at `.` with write permissions.

---

## ☠️ Level 4: The "Singularity Risk" (91-100/100)
*Wild, possibly dangerous, hypothetical scenarios. Proceed with caution.*

24. **The "Startup Founder" (92/100)**
    *   **Goal**: "Build a SAAS that sells cat pictures."
    *   **How**: Recursive Strategy. Planner creates Frontend, Backend, Stripe, Deployment tasks.
    *   **Output**: A fully deployed web app.

25. **Reverse Engineer (94/100)**
    *   **Goal**: Decompile a binary, analyze assembly, rewrite in C.
    *   **How**: Agent with `ghidra` (headless) or `objdump`.

26. **Operating System Manager (95/100)**
    *   **Goal**: "Clean up my Mac."
    *   **How**: Agent with `sudo` access (EXTREMELY DANGEROUS). Deletes huge files, kills processes.

27. **Prompt Optimizer Loop (96/100)**
    *   **Goal**: AB Test system prompts. Agent A writes prompts for Agent B. Agent C judges Agent B options.
    *   **How**: Evolutionary swarm topology.

28. **Language Creator (98/100)**
    *   **Goal**: "Invent a new programming language and escreatethe compiler in Python."
    *   **How**: Recursive strategy. Design syntax -> Write Parser -> Write Emitter.

29. **Codebase Mutation (99/100)**
    *   **Goal**: "Optimize Kirosu's core execution loop by rewriting it in Rust/C extension."
    *   **How**: Agent reads Python `agent.py`, writes Rust binding, compiles, replaces original.

30. **Self-Replication (100/100)**
    *   **Goal**: "Deploy Kirosu to a new AWS instance, SSH in, and start a new Swarm there."
    *   **How**: Agent with Terraform/SSH keys. It spreads itself to new servers to increase compute.

---

# Enable God Mode
export KIRO_PROVIDER=codex
kirosu agent --trust-all-tools
```

---

## 🦄 Level 5: The "Wilder" (Real Life Quirks)
*Hyper-specific automation for personal or niche chaos. (Feasible today)*

31. **The "Unsubscribe" Agent**
    *   **Goal**: Scan Gmail (via API) for "unsubscribe" links in unread promo emails. Click them.
    *   **How**: Agent + Gmail API + Requests.

32. **Apartment Hunter Swarm**
    *   **Goal**: Monitor Zillow/Craigslist every 5m. Filter by "Commute time < 30m" (GMaps API). Text user instantly.
    *   **How**: Parallel Scraper Agents + Twilio API.

33. **The "Travel Agent"**
    *   **Goal**: Monitor 50 specific flight routes. If price dips below $X, execute a provisional booking (mock or real).
    *   **How**: Selenium/Playwright Agent running headless.

34. **Resume Tailor**
    *   **Goal**: Read a Job Description URL. Rewrite your PDF resume's summary to match keywords perfectly. Submit.
    *   **How**: PDF reader tool + Writer Agent + Puppeteer for submission forms.

35. **Spotify Curator**
    *   **Goal**: Scrape Pitchfork/Fantano reviews. Match with your listening history. Build a "High Critical Acclaim" playlist.
    *   **How**: Spotify API + Web Search Agent.

36. **Grocery Optimizer**
    *   **Goal**: OCR local supermarket fliers. Plan meal prep based on discounts. Output Instacart cart.
    *   **How**: Vision Model Agent -> Planner Agent.

37. **Legal Contract Scanner**
    *   **Goal**: Read 50-page PDF contracts. Highlight "Indemnification" and "Non-Compete" clauses in red.
    *   **How**: Text extraction + Analysis Agent.

38. **Family IT Support**
    *   **Goal**: "Grandma's Printer is down". SSH into family server/Pi. Check CUPS logs. Restart service.
    *   **How**: Agent with SSH keys to remote helper device.

39. **Crypto Arbitrage Watcher (Real Money)**
    *   **Goal**: Watch 5 exchanges. If Price A < Price B by 2%, execute buy/sell.
    *   **How**: High-speed loop agent (Codex) + Exchange APIs.

40. **Meeting Notes Autopilot**
    *   **Goal**: Listen to Zoom audio (Whisper). Draft Notion page. Assign Jira tasks to attendees mentioned.
    *   **How**: Audio processing -> Text -> API calls.

---

## 🚀 Level 6: The "Ambitious" (Enterprise Scale)
*Entire departments automated into a background process.*

41. **Cloud Migration Swarm**
    *   **Goal**: Scan AWS resources. Write equivalent Terraform for Azure. Flag incompatibilities.
    *   **How**: Recursive Strategy (Planner -> Resource Mappers).

42. **GDPR "Right to be Forgotten" Executor**
    *   **Goal**: User clicks "Delete" -> Agent triggers data wiping across 50 microservices/DBs.
    *   **How**: Message Queue listener -> Agent Swarm.

43. **Competitor Watchtower**
    *   **Goal**: Monitor 10 competitor landing pages daily. If H1/Pricing changes, diff it and Slack the Product Team.
    *   **How**: Visual Regression Testing Agent.

44. **SaaS Cost Killer**
    *   **Goal**: Scan AWS for unattached EBS volumes and Idle EC2s. Kill them. Report savings.
    *   **How**: "Dangerous Mode" Agent with AWS CLI.

45. **Release Manager AI**
    *   **Goal**: Verify CI passing. Merge develop->main. Tag release. Generate Changelog from commits. Deploy.
    *   **How**: GitHub API Agent + Deployment pipeline integration.

46. **Database Schema Normalizer**
    *   **Goal**: Analyze 100 tables. Find denormalized redundanies. Suggest 3NF schema. Write migration SQL.
    *   **How**: Database Introspection Agent.

47. **Full-App Localization**
    *   **Goal**: 50 Agents. Each takes one UI screen. Translates to Japanese. Verifies layout doesn't break.
    *   **How**: Huge Parallel Swarm (Map-Reduce).

48. **Support Ticket Triage (Tier 1)**
    *   **Goal**: Read incoming tickets. Auto-reply to "Password Reset". Escalate "Server Down" to PagerDuty.
    *   **How**: Webhook listener -> Classification Agent.

49. **Documentation Archaeologist**
    *   **Goal**: Compare Confluence docs vs Codebed. Flag "Stale Docs" referring to deleted API parameters.
    *   **How**: Knowledge Base indexing -> Code search.

50. **Sales Lead Qualifier**
    *   **Goal**: Scrape LinkedIn for 500 leads. Score by company size. Enrich CRM data. Email top 10%.
    *   **How**: Research Agent Swarm.

---

## ⚡ Level 7: The "Godlike" (High Impact/Leverage)
*Systems that manage themselves. The dream of AGI in operations.*

51. **The "CTO" Agent**
    *   **Goal**: Read every PR title in the org daily. Detect "Technological Drift" (e.g. "Why are we adding PHP?"). Alert leadership.
    *   **How**: Metadata Analysis Agent running nightly.

52. **Self-Healing Incident Commander**
    *   **Goal**: Detect 500 error spike. SSH to server. Grep logs. See "Out of Memory". Restart Pod. Update StatusPage.
    *   **How**: "Dangerous Mode" Agent hooked to Prometheus alerts.

53. **Legacy Database Strangler**
    *   **Goal**: Intercept SQL queries. Dual-write to new Mongo/Postgres. Verify parity. Switch read-path automatically.
    *   **How**: Proxy Agent + Verification Swarm.

54. **The "Venture Capitalist" Analyst**
    *   **Goal**: Scrape ProductHunt/TechCrunch. Summarize trends. Predict "Next Big Thing" based on keyword velocity.
    *   **How**: Big Data Analysis Agent.

55. **Continuous Penetration Testing**
    *   **Goal**: A permanent swarm attacking your Staging environment 24/7 using newly published CVEs.
    *   **How**: Security Agent with Metasploit/Nmap tools.

56. **White-Label SaaS Spawner**
    *   **Goal**: Input: Logo, Domain, Color. Output: Deployed K8s namespace, DNS records, branded UI.
    *   **How**: Infrastructure-as-Code Agent.

57. **Data Warehouse Architect**
    *   **Goal**: Look at raw JSON dumps in S3. Infer schema. Create Snowflake tables. Build Airbyte pipelines.
    *   **How**: Schema Inference Agent.

58. **Supply Chain Sentinel**
    *   **Goal**: Read news ("Earthquake in Taiwan"). Query ERP for parts from Taiwan. Alert Procurement Manager.
    *   **How**: News Monitoring Agent + ERP SQL Agent.

59. **The "Lobbyist"**
    *   **Goal**: Monitor government bill texts. Flag legislation affecting your specific industry.
    *   **How**: Regulatory Text Analysis Agent.

60. **Universal API Wrapper**
    *   **Goal**: "Here is an undocumented API endpoint". Agent proxies traffic, infers types, generates a Python SDK library.
    *   **How**: Traffic Analysis -> Code Gen Agent.
