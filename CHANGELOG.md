# Changelog

## [1.1.0](https://github.com/memes/terraform-google-private-gke-cluster/compare/v1.0.2...v1.1.0) (2023-08-27)


### Features

* Options for public master endpoint and SNAT ([29c8043](https://github.com/memes/terraform-google-private-gke-cluster/commit/29c8043af1d344ebb8efbded7f7421b78f7d7aac))


### Bug Fixes

* Change default description for Autopilot ([45bc897](https://github.com/memes/terraform-google-private-gke-cluster/commit/45bc897dd7ed19eeeef7efeb14ded4754b87aacf))
* Do not recreate Autopilot clusters ([2e394c1](https://github.com/memes/terraform-google-private-gke-cluster/commit/2e394c195dabce2e6e61b9af00807539b563df7f))
* Update GKE SA roles ([7bb862e](https://github.com/memes/terraform-google-private-gke-cluster/commit/7bb862ed5b4b20497fc54d9efafda73242ff7431))
* Use intended service account for Autopilot ([ff075db](https://github.com/memes/terraform-google-private-gke-cluster/commit/ff075db72ba0ed1ad04c34cc1e57d28f5be567a2))

## [1.0.2](https://github.com/memes/terraform-google-private-gke-cluster/compare/v1.0.1...v1.0.2) (2023-04-07)


### Bug Fixes

* Cluster_id could be a region or a zone ([bf2356d](https://github.com/memes/terraform-google-private-gke-cluster/commit/bf2356d0a82f24511456080ece7acb25d3858d74)), closes [#11](https://github.com/memes/terraform-google-private-gke-cluster/issues/11)
* **sa:** Valid GAR repos failed validation ([5ae6a0d](https://github.com/memes/terraform-google-private-gke-cluster/commit/5ae6a0d942ca9fd32c0d49d339f94702ce2f3021))

## [1.0.1](https://github.com/memes/terraform-google-private-gke-cluster/compare/v1.0.0...v1.0.1) (2023-04-06)


### Bug Fixes

* **kubeconfig:** Constrain google provider &gt;= 4.52 ([3dfeced](https://github.com/memes/terraform-google-private-gke-cluster/commit/3dfeced56c454715ab9f353bb06d5853f41eda02))

## 1.0.0 (2023-02-13)


### Features

* Private GKE cluster module ([0e8455d](https://github.com/memes/terraform-google-private-gke-cluster/commit/0e8455d2bd2778e96fe2433f00c9dbd064fba41f))

## Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
