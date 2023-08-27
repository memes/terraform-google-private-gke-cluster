# frozen_string_literal: true

# rubocop:disable Metrics/BlockLength
control 'node_pools' do
  title 'Ensure GKE node pools meet expectations'
  impact 1.0
  project_id = input('input_project_id')
  service_account = input('output_service_account')
  location = input('output_location')
  cluster_name = input('output_name')
  node_pools = JSON.parse(input('output_node_pools_json'), { symbolize_names: true })
  expected_labels = { 'terraform_module' => 'private-gke-cluster' }
                    .merge(JSON.parse(input('output_labels_json'), { symbolize_names: false }))

  only_if('Autopilot node pools are not configured by module') do
    !input('output_is_autopilot')
  end

  node_pools_matcher = /^(?:#{node_pools.keys.join('|')})-\d+$/
  describe google_container_node_pools(project: project_id, location: location,
                                       cluster_name: cluster_name).where(node_pool_name: node_pools_matcher) do
    its('count') { should eq node_pools.keys.count }
  end
  google_container_node_pools(project: project_id, location: location,
                              cluster_name: cluster_name).where(node_pool_name: node_pools_matcher).node_pool_names.each do |name| # rubocop:disable Layout/LineLength
    key = name.gsub(/-\d+$/, '')
    expected = node_pools[key.to_sym]
    describe google_container_node_pool(project: project_id, location: location, cluster_name: cluster_name,
                                        nodepool_name: name) do
      it { should exist }
      its('config.machine_type') { should cmp expected[:machine_type] }
      its('config.disk_size_gb') { should cmp expected[:disk_size] }
      its('config.oauth_scopes') { should cmp ['https://www.googleapis.com/auth/cloud-platform'] }
      its('config.service_account') { should cmp service_account }
      its('config.metadata') do
        should cmp Hash['node_pool' => key, 'cluster_name' => cluster_name,
                        'disable-legacy-endpoints' => 'true'].merge(expected[:metadata] || {})
      end
      its('config.image_type') { should cmp expected[:image_type] }
      its('config.labels') { should cmp expected_labels.merge({ 'node_pool' => key, 'cluster_name' => cluster_name }) }
      its('config.tags') { should cmp(expected[:tags].nil? || expected[:tags].empty? ? nil : expected[:tags]) } unless
      its('config.preemptible') { should cmp expected[:preemptible] }
      its('config.disk_type') { should cmp expected[:disk_type] }
      its('config.min_cpu_platform') do
        should cmp(expected[:min_cpu_platform].nil? || expected[:min_cpu_platform].empty? ? nil : expected[:min_cpu_platform]) # rubocop:disable Layout/LineLength
      end
      its('config.taints') { should cmp(expected[:taints].nil? || expected[:taints].empty? ? nil : expected[:taints]) }
      its('config.shielded_instance_config.enable_secure_boot') do
        should cmp(expected[:enable_secure_boot] ? true : nil)
      end
      if expected[:enable_integrity_monitoring]
        its('config.shielded_instance_config.enable_integrity_monitoring') { should cmp true }
      else
        its('config.shielded_instance_config.enable_integrity_monitoring') { should be_nil }
      end
      its('config.workload_meta_config.mode') { should cmp 'GKE_METADATA' }
      its('status') { should cmp 'RUNNING' }
      its('initial_node_count') { should cmp expected[:min_nodes_per_zone] }
      if expected[:autoscaling]
        its('autoscaling.enabled') { should cmp true }
        its('autoscaling.min_node_count') { should cmp expected[:min_nodes_per_zone] }
        its('autoscaling.max_node_count') { should cmp expected[:max_nodes_per_zone] }
      else
        its('autoscaling.enabled') { should be_nil }
      end
      its('management.auto_upgrade') { should cmp expected[:auto_upgrade] }
      its('management.auto_repair') { should cmp expected[:auto_repair] }
    end
  end
end
# rubocop:enable Metrics/BlockLength

# rubocop:disable Metrics/BlockLength
control 'nap_pools' do
  title 'Ensure GKE auto-provisioned node pools meet expectations'
  impact 1.0
  project_id = input('input_project_id')
  service_account = input('output_service_account')
  location = input('output_location')
  cluster_name = input('output_name')
  autoscaling = JSON.parse(input('output_autoscaling_json'), { symbolize_names: true })

  only_if('Node autoprovisioning is not enabled') do
    !(autoscaling.nil? || autoscaling.empty? || autoscaling[:nap].nil? || autoscaling[:nap].empty?)
  end

  expected = autoscaling[:nap]
  describe google_container_node_pools(project: project_id, location: location,
                                       cluster_name: cluster_name).where(node_pool_name: /^nap-e2-/) do
    its('count') { should be_positive }
  end
  google_container_node_pools(project: project_id, location: location,
                              cluster_name: cluster_name).where(node_pool_name: /^nap-e2-/).node_pool_names.each do |name| # rubocop:disable Layout/LineLength
    describe google_container_node_pool(project: project_id, location: location, cluster_name: cluster_name,
                                        nodepool_name: name) do
      it { should exist }
      its('config.min_cpu_platform') do
        should cmp(expected[:min_cpu_platform].nil? || expected[:min_cpu_platform].empty? ? nil : expected[:min_cpu_platform]) # rubocop:disable Layout/LineLength
      end
      its('config.disk_size_gb') { should cmp expected[:disk_size] }
      its('config.oauth_scopes') { should cmp ['https://www.googleapis.com/auth/cloud-platform'] }
      its('config.service_account') { should cmp service_account }
      its('config.metadata') { should cmp Hash['disable-legacy-endpoints' => 'true'] }
      its('config.image_type') { should cmp expected[:image_type] }
      its('config.tags') { should cmp(expected[:tags].nil? || expected[:tags].empty? ? nil : expected[:tags]) }
      its('config.disk_type') { should cmp expected[:disk_type] }
      if its('config.shielded_instance_config.enable_integrity_monitoring') do
        should cmp(expected[:enable_integrity_monitoring] ? true : nil)
      end
        its('config.shielded_instance_config.enable_secure_boot') do
          should cmp(expected[:enable_secure_boot] ? true : nil)
        end
      end
      its('status') { should cmp 'RUNNING' }
      its('management.auto_upgrade') { should cmp expected[:auto_upgrade] }
      its('management.auto_repair') { should cmp expected[:auto_repair] }
    end
  end
end
# rubocop:enable Metrics/BlockLength
