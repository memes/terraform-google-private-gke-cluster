# This makefile implements wrappers around various kitchen test commands. The
# intent is to make it easy to execute a full test suite, or individual actions,
# with a safety net that ensures the test harness is present before executing
# kitchen commands. Specifically, Terraform in /test/setup/ has been applied, and
# the examples have been cloned to an ephemeral folder and source modified to
# use these local files.
#
# Every kitchen command has an equivalent target; kitchen action [pattern] becomes
# make action[.pattern]
#
# E.g.
#   kitchen test                 =>   make test
#   kitchen verify default       =>   make verify.default
#   kitchen converge meta        =>   make converge.meta
#
# Default target will create necessary test harness, then launch kitchen test
.DEFAULT: test

# TODO @memes - kitchen-terraform requires use of terraform executable, switch
# to tofu when tests are modified
TF_EXECUTABLE := terraform
TF_SETUP_SENTINEL := test/setup/harness.tfvars

.PHONY: test
test: $(TF_SETUP_SENTINEL)
	kitchen test

.PHONY: test.%
test.%: $(TF_SETUP_SENTINEL)
	kitchen test $*

.PHONY: destroy
destroy: $(TF_SETUP_SENTINEL)
	kitchen destroy

.PHONY: destroy.%
destroy.%: $(TF_SETUP_SENTINEL)
	kitchen destroy $*

.PHONY: verify
verify: $(TF_SETUP_SENTINEL)
	kitchen verify

.PHONY: verify.%
verify.%: $(TF_SETUP_SENTINEL)
	kitchen verify $*

.PHONY: converge
converge: $(TF_SETUP_SENTINEL)
	kitchen converge

.PHONY: converge.%
converge.%: $(TF_SETUP_SENTINEL)
	kitchen converge $*

EXAMPLES :=

$(TF_SETUP_SENTINEL): $(wildcard test/setup/*.tf) $(filter-out $(TF_SETUP_SENTINEL), $(wildcard test/setup/*.tfvars)) $(addprefix test/ephemeral/,$(addsuffix /main.tf,$(EXAMPLES)))
	$(TF_EXECUTABLE) -chdir=$(@D) init -input=false
	$(TF_EXECUTABLE) -chdir=$(@D) apply -input=false -auto-approve -target random_pet.prefix -target random_shuffle.zones
	$(TF_EXECUTABLE) -chdir=$(@D) apply -input=false -auto-approve

# We want the examples to use the registry tagged versions of the module, but
# need to test against the local code. Make an ephemeral copy of each example
# with the source redirected to local module
test/ephemeral/%/main.tf: $(wildcard examples/%/*.tf)
	mkdir -p $(@D)
	rsync -avP --exclude .terraform \
		--exclude .terraform.lock.hcl \
		--exclude 'terraform.tfstate' \
		examples/$*/ $(@D)/
	sed -i '' -E -e '1h;2,$$H;$$!d;g' -e 's@module "cluster"[ \t]*{[ \t]*\n[ \t]*source[ \t]*=[ \t]*"[^"]+"@module "cluster" {\n  source = "../../../"@' $@
	sed -i '' -E -e '1h;2,$$H;$$!d;g' -e 's@module "autopilot"[ \t]*{[ \t]*\n[ \t]*source[ \t]*=[ \t]*"[^"]+"@module "autopilot" {\n  source = "../../../modules/autopilot/"@g' $@
	sed -i '' -E -e '1h;2,$$H;$$!d;g' -e 's@module "kubeconfig"[ \t]*{[ \t]*\n[ \t]*source[ \t]*=[ \t]*"[^"]+"@module "kubeconfig" {\n  source = "../../../modules/kubeconfig/"@g' $@
	sed -i '' -E -e '1h;2,$$H;$$!d;g' -e 's@module "sa"[ \t]*{[ \t]*\n[ \t]*source[ \t]*=[ \t]*"[^"]+"@module "sa" {\n  source = "../../../modules/sa/"@g' $@

.PHONY: clean
clean: $(wildcard $(TF_SETUP_SENTINEL))
	-if test -n "$<" && test -f "$<"; then kitchen destroy; fi
	if test -n "$<" && test -f "$<"; then $(TF_EXECUTABLE) -chdir=$(<D) destroy -auto-approve; fi

.PHONY: realclean
realclean: clean
	if test -d generated; then find generated -depth 1 -type d -exec rm -rf {} +; fi
	if test -d test/reports; then find test/reports -depth 1 -type d -exec rm -rf {} +; fi
	if test -d test/ephemeral; then find test/ephemeral -depth 1 -type d -exec rm -rf {} +; fi
	find . -type d -name .terraform -exec rm -rf {} +
	find . -type d -name terraform.tfstate.d -exec rm -rf {} +
	find . -type f -name .terraform.lock.hcl -exec rm -f {} +
	find . -type f -name terraform.tfstate -exec rm -f {} +
	find . -type f -name terraform.tfstate.backup -exec rm -f {} +
	rm -rf .kitchen

# Helper to ensure code is ready for tagging
# 1. Tag is a valid semver with v prefix (e.g. v1.0.0)
# 1. Git tree is clean
# 2. Each example is using a memes GitHub source and the version matches
#    the tag to be applied
# 3. Inspec controls have version matching the tag
# if all those pass indicate success
.PHONY: pre-release.%
pre-release.%:
	@echo '$*' | grep -Eq '^v([0-9]+\.){2}[0-9]+$$' || \
		(echo "Tag doesn't meet requirements"; exit 1)
	@test "$(shell git status --porcelain | wc -l | grep -Eo '[0-9]+')" -eq 0 || \
		(echo "Git tree is unclean"; exit 1)
	@test -d examples && \
	    find examples -type f -name main.tf -print0 | \
		xargs -0 awk 'BEGIN{m=0;s=0;v=0}; /module "cluster"/ {m=1}; m==1 && /source[ \t]*=[ \t]*"memes\/private-gke-cluster\/google/ {s++}; m==1 && /version[ \t]*=[ \t]*"$(subst .,\.,$(*:v%=%))"/ {v++}; END{if (s==0) { printf "%s has incorrect source\n", FILENAME}; if (v==0) { printf "%s has incorrect version\n", FILENAME}; if (s==0 || v==0) { exit 1}}'
	@test -d examples && \
	    find examples -type f -name main.tf -print0 | \
		xargs -0 awk 'BEGIN{m=0;s=0;v=0}; /module "autopilot"/ {m=1}; m==1 && /source[ \t]*=[ \t]*"memes\/private-gke-cluster\/google\/\/modules\/autopilot/ {s++}; m==1 && /version[ \t]*=[ \t]*"$(subst .,\.,$(*:v%=%))"/ {v++}; END{if (s==0) { printf "%s has incorrect source\n", FILENAME}; if (v==0) { printf "%s has incorrect version\n", FILENAME}; if (s==0 || v==0) { exit 1}}'
	@test -d examples && \
	    find examples -type f -name main.tf -print0 | \
		xargs -0 awk 'BEGIN{m=0;s=0;v=0}; /module "kubeconfig"/ {m=1}; m==1 && /source[ \t]*=[ \t]*"memes\/private-gke-cluster\/google\/\/modules\/kubeconfig/ {s++}; m==1 && /version[ \t]*=[ \t]*"$(subst .,\.,$(*:v%=%))"/ {v++}; END{if (s==0) { printf "%s has incorrect source\n", FILENAME}; if (v==0) { printf "%s has incorrect version\n", FILENAME}; if (s==0 || v==0) { exit 1}}'
	@test -d examples && \
	    find examples -type f -name main.tf -print0 | \
		xargs -0 awk 'BEGIN{m=0;s=0;v=0}; /module "sa"/ {m=1}; m==1 && /source[ \t]*=[ \t]*"memes\/private-gke-cluster\/google\/\/modules\/sa/ {s++}; m==1 && /version[ \t]*=[ \t]*"$(subst .,\.,$(*:v%=%))"/ {v++}; END{if (s==0) { printf "%s has incorrect source\n", FILENAME}; if (v==0) { printf "%s has incorrect version\n", FILENAME}; if (s==0 || v==0) { exit 1}}'
	@grep -Eq '^version:[ \t]*$(subst .,\.,$(*:v%=%))[ \t]*$$' test/profiles/access/inspec.yml || \
		(echo "test/profiles/access/inspec.yml has incorrect tag"; exit 1)
	@grep -Eq '^version:[ \t]*$(subst .,\.,$(*:v%=%))[ \t]*$$' test/profiles/cluster/inspec.yml || \
		(echo "test/profiles/cluster/inspec.yml has incorrect tag"; exit 1)
	@grep -Eq '^version:[ \t]*$(subst .,\.,$(*:v%=%))[ \t]*$$' test/profiles/sa/inspec.yml || \
		(echo "test/profiles/sa/inspec.yml has incorrect tag"; exit 1)
	@echo 'Source is ready to release $*'
