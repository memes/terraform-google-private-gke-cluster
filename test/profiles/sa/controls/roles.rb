# frozen_string_literal: true

control 'project' do
  title 'Ensure GKE service account has appropriate roles on the project'
  impact 1.0
  project_id = input('input_project_id')
  member = input('output_member')

  %w[roles/logging.logWriter roles/monitoring.metricWriter roles/monitoring.viewer
     roles/stackdriver.resourceMetadata.writer].each do |role|
    describe google_project_iam_binding(project: project_id, role:) do
      it { should exist }
      its('members') { should include member }
    end
  end
end

control 'gcr_role' do
  title 'Ensure GKE service account has role on backing storage for GCR repos'
  impact 0.5
  member = input('output_member')
  repos = JSON.parse(input('output_repositories_json'), { symbolize_names: false }).select do |repo|
    repo.match?(/^(?:(?:asia|eu|us)\.)?gcr.io/)
  end

  only_if('GCR access was not requested') do
    repos.count.positive?
  end

  repos.each do |repo|
    # GCR repos use buckets for the objects; SA should have storage.objectViewer
    # on it.
    repo_params = repo.match(%r{^(?<location>[^.]+\.)?gcr.io/(?<name>[^/]+)}).named_captures
    bucket = "#{repo_params['location']}artifacts.#{repo_params['name']}.appspot.com"
    describe google_storage_bucket_iam_binding(bucket:, role: 'roles/storage.objectViewer') do
      it { should exist }
      its('members') { should include member }
    end
  end
end

control 'gar_role' do
  title 'Ensure GKE service account has role to access GAR repos'
  impact 0.5
  member = input('output_member')
  repos = JSON.parse(input('output_repositories_json'), { symbolize_names: false }).select do |repo|
    repo.match?(%r{^[a-z]{2,}(?:-[a-z]+[1-9])?-docker\.pkg\.dev/[^/]+/[^/]+})
  end

  # inspec-gcp doesn't have a resource for GAR yet
  # github.com/inspect/inspec-gcp/issues/294
  only_if('GAR inspec resource is unavailable') do
    false
  end

  only_if('GAR access was not requested') do
    repos.count.positive?
  end

  repos.each do |repo|
    repo_params = repo.match(%r{
      ^(?<location>[a-z]{2,}(?:-[a-z]+[1-9])?)-docker.pkg.dev/
      (?<project>[^/]+)/
      (?<name>[^/]+)
      }x).named_captures
    describe google_ARTIFACT_REGISTRY_iam_binding(project: repo_params['project'], location: repo_params['location'],
                                                  name: repo_params['name']) do
      it { should exist }
      its('members') { should include member }
    end
  end
end
