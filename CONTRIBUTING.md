# Contributing

1. Fork the repository and create a branch (`git checkout -b feature/short-name`).
2. Run `scripts/setup.sh`, then `cd backend && pytest` and `cd frontend && npm test` before and after your change.
3. Keep changes focused: one purpose per commit, short imperative messages (`add latency fault to proxy`).
4. Follow the layout rules: routes call services, services call repositories, no business logic in React components,
   metrics are computed only in `backend/app/metrics`, AI code never touches the proxy, database or target.
5. Add tests for fault rules, metric maths and any new endpoint.
6. Never commit `.env`, secrets or database files. Open a pull request describing the change and how you tested it.
