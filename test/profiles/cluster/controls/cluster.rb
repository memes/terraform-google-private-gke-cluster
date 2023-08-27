# frozen_string_literal: true

# rubocop:disable Metrics/BlockLength
control 'cluster' do
  title 'Ensure private GKE cluster meets expectations'
  impact 1.0
  project_id = input('input_project_id')
  expected_name = input('input_name')
  location = input('output_location')
  name = input('output_name')
  subnet = JSON.parse(input('output_subnet_json'), { symbolize_names: true })
  options = JSON.parse(input('output_options_json'), { symbolize_names: true })
  features = JSON.parse(input('output_features_json'), { symbolize_names: true })
  master_authorized_networks = JSON.parse(input('output_master_authorized_networks_json'), { symbolize_names: true })
  is_autopilot = input('output_is_autopilot')
  expected_labels = { 'cluster_name' => name,
                      'terraform_module' => is_autopilot ? 'private-gke-cluster_autopilot' : 'private-gke-cluster' }
                    .merge(JSON.parse(input('output_labels_json'), { symbolize_names: false }))

  describe google_container_cluster(project: project_id, location: location, name: name) do
    it { should exist }
    its('name') { should cmp expected_name }
    its('initial_node_count') { should cmp(is_autopilot ? nil : 1) }
    its('master_auth.username') { should be_nil }
    its('master_auth.password') { should be_nil }
    its('master_auth.client_certificate_config.issue_client_certificate') { should be_nil }
    its('master_auth.client_certificate') { should be_nil }
    its('master_auth.client_key') { should be_nil }
    its('logging_service') { should cmp 'logging.googleapis.com/kubernetes' }
    its('monitoring_service') { should cmp 'monitoring.googleapis.com/kubernetes' }
    its('database_encryption.state') { should cmp options[:kms].nil? ? 'DECRYPTED' : 'ENCRYPTED' }
    its('database_encryption.key_name') { should cmp options[:kms] }
    its('private_cluster_config.enable_private_nodes') { should cmp true }
    if options[:private_endpoint]
      its('private_cluster_config.enable_private_endpoint') { should cmp true }
    else
      its('private_cluster_config.enable_private_endpoint') { should be_nil }
    end
    its('private_cluster_config.master_ipv4_cidr_block') { should cmp subnet[:master_cidr] }
    its('private_cluster_config.private_endpoint') { should_not be_nil }
    its('enable_tpu') { should cmp(features[:tpu] ? true : nil) }
    its('addons_config.http_load_balancing.disabled') { should cmp(is_autopilot || features[:l7_lb] ? nil : true) }
    its('addons_config.horizontal_pod_autoscaling.disabled') { should cmp(is_autopilot || features[:hpa] ? nil : true) }
    its('addons_config.kubernetes_dashboard.disabled') { should cmp true }
    its('addons_config.network_policy_config.disabled') { should cmp true }
    its('addons_config.gce_persistent_disk_csi_driver_config.enabled') do
      should cmp(is_autopilot || features[:csi_gce_pd] ? true : nil)
    end
    its('subnetwork') { should cmp subnet[:self_link].split('/').last }
    its('resource_labels') { should cmp expected_labels }
    its('legacy_abac.enabled') { should be_nil }
    its('network_policy.enabled') { should be_nil }
    its('default_max_pods_constraint.max_pods_per_node') do
      should cmp(is_autopilot ? 110 : options[:max_pods_per_node])
    end
    its('ip_allocation_policy.use_ip_aliases') { should cmp true }
    its('ip_allocation_policy.create_subnetwork') { should be_nil }
    its('ip_allocation_policy.subnetwork_name') { should be_nil }
    its('ip_allocation_policy.cluster_secondary_range_name') { should cmp subnet[:pods_range_name] }
    its('ip_allocation_policy.services_secondary_range_name') { should cmp subnet[:services_range_name] }
    its('ip_allocation_policy.cluster_ipv4_cidr_block') { should_not be_nil }
    its('ip_allocation_policy.node_ipv4_cidr_block') { should be_nil }
    its('ip_allocation_policy.services_ipv4_cidr_block') { should_not be_nil }
    its('ip_allocation_policy.tpu_ipv4_cidr_block') { should be_nil }
    its('status') { should be_in %w[RUNNING RECONCILING] }
    if options[:private_endpoint]
      its('master_authorized_networks_config.enabled') { should cmp true }
      its('master_authorized_networks_config.cidr_blocks.count') { should eq 1 }
      its('master_authorized_networks_config.cidr_blocks.first.cidr_block') do
        should cmp master_authorized_networks[0][:cidr_block]
      end
    end
    its('binary_authorization.enabled') { should cmp(features[:binary_authorization] ? true : nil) }
    if options[:release_channel] == 'UNSPECIFIED'
      its('release_channel.channel') { should be_nil }
      its('initial_cluster_version') { should match(/^#{options[:version]}/) }
    else
      its('release_channel.channel') { should cmp options[:release_channel] }
    end
    # shielded nodes
    # network config
    its('enable_kubernetes_alpha') { should cmp(is_autopilot || !features[:alpha] ? nil : true) }
    its('location') { should cmp subnet[:self_link].split('/').reverse[2] }
  end
end
# rubocop:enable Metrics/BlockLength
