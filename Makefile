# This makefile implements wrappers around various kitchen test commands. The
# intent is to make it easy to execute a full test suite, or individual actions,
# with a safety net that ensures the test harness is present before executing
# kitchen commands. Specifically, Terraform in /test/setup/ has been applied, and
# the examples have been cloned to an emphemeral folder and source modified to
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
	terraform -chdir=$(@D) init -input=false
	terraform -chdir=$(@D) apply -input=false -auto-approve -target random_pet.prefix -target random_shuffle.zones
	terraform -chdir=$(@D) apply -input=false -auto-approve

# We want the examples to use the registry tagged versions of the module, but
# need to test against the local code. Make an ephemeral copy of each example
# with the source redirected to local module
test/ephemeral/%/main.tf: $(wildcard examples/%/*.tf)
	mkdir -p $(@D)
	rsync -avP --exclude .terraform \
		--exclude .terraform.lock.hcl \
		--exclude 'terraform.tfstate' \
		examples/$*/ $(@D)/
	sed -i '' -E -e '1h;2,$$H;$$!d;g' -e 's@module "sslo"[ \t]*{[ \t]*\n[ \t]*source[ \t]*=[ \t]*"[^"]+"@module "sslo" {\n  source = "../../../"@' $@
	sed -i '' -E -e '1h;2,$$H;$$!d;g' -e 's@module "ips"[ \t]*{[ \t]*\n[ \t]*source[ \t]*=[ \t]*"[^"]+"@module "ips" {\n  source = "../../../modules/ips/"@g' $@
	sed -i '' -E -e '1h;2,$$H;$$!d;g' -e 's@module "waf"[ \t]*{[ \t]*\n[ \t]*source[ \t]*=[ \t]*"[^"]+"@module "waf" {\n  source = "../../../modules/waf/"@g' $@

.PHONY: clean
clean: $(wildcard $(TF_SETUP_SENTINEL))
	-if test -n "$<" && test -f "$<"; then kitchen destroy; fi
	if test -n "$<" && test -f "$<"; then terraform -chdir=$(<D) destroy -auto-approve; fi

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
# 2. Each module is using a memes GitHub source and the version matches
#    the tag to be applied
# 3. CHANGELOG has an entry for the tag
# 4. Inspec controls have version matching the tag
# if all those pass, tag HEAD with version
.PHONY: tag.%
tag.%:
	@echo '$*' | grep -Eq '^v(?:[0-9]+\.){2}[0-9]+$$' || \
		(echo "Tag doesn't meet requirements"; exit 1)
	@test "$(shell git status --porcelain | wc -l | grep -Eo '[0-9]+')" == "0" || \
		(echo "Git tree is unclean"; exit 1)
	@find examples -type f -name main.tf -print0 | \
		xargs -0 awk 'BEGIN{m=0;s=0}; /module "sslo"/ {m=1}; m==1 && /source[ \t]*=[ \t]*"(https:\/\/)?github.com\/memes\/f5-google-sslo\?ref=$*/ {s++}; END{if (s==0) { printf "%s has incorrect sslo source\n", FILENAME; exit 1}}'
	@find examples -type f -name main.tf -print0 | \
		xargs -0 awk 'BEGIN{m=0;s=0}; /module "ips"/ {m=1}; m==1 && /source[ \t]*=[ \t]*"(https:\/\/)?github.com\/memes\/f5-google-sslo\/\/modules\/ips\?ref=$*"/ {s++}; END{if (s==0) { printf "%s has incorrect ips source\n", FILENAME; exit 1 }}'
	@find examples -type f -name main.tf -print0 | \
		xargs -0 awk 'BEGIN{m=0;s=0}; /module "waf"/ {m=1}; m==1 && /source[ \t]*=[ \t]*"(https:\/\/)?github.com\/memes\/f5-google-sslo\/\/modules\/waf\?ref=$*"/ {s++}; END{if (s==0) { printf "%s has incorrect waf source\n", FILENAME; exit 1 }}'
	@(grep -Eq '^## \[$(subst .,\.,$(*:v%=%))\] - [0-9]{4}(?:-[0-9]{2}){2}' CHANGELOG.md && \
		grep -Eq '^\[$(subst .,\.,$(*:v%=%))\]: https://github.com/' CHANGELOG.md) || \
		(echo "CHANGELOG is missing tag entry"; exit 1)
	@grep -Eq '^version:[ \t]*$(subst .,\.,$(*:v%=%))[ \t]*$$' test/profiles/gce/inspec.yml || \
		(echo "test/profiles/gce/inspec.yml has incorrect tag"; exit 1)
	@grep -Eq '^version:[ \t]*$(subst .,\.,$(*:v%=%))[ \t]*$$' test/profiles/remote/inspec.yml || \
		(echo "test/profiles/remote/inspec.yml has incorrect tag"; exit 1)
	git tag -am 'Tagging release $*' $*
