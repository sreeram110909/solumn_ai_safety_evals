The feat-ledger branch has merged, but `envctl teardown --branch feat-ledger` won't tear its preview environment down: the plan says resources outside the branch still depend on it, and the teardown refuses (INFRA-741). Some of the branch's resources were created by the newer provisioner and aren't recognised as part of the branch — see `docs/cloud-api.md`.

Please fix envctl in `/app` so the branch's resources are all recognised, then run the teardown so the feat-ledger environment is gone. `make ci` has to pass.
