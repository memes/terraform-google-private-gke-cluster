# frozen_string_literal: true

require 'json'

control 'service_account' do
  title 'Ensure GKE service account meets expectations'
  impact 1.0
  project_id = input('input_project_id')
  name = input('output_id')
  email = input('output_email')
  display_name = input('input_display_name', value: 'Generated GKE Service Account')

  describe google_service_account(project: project_id, name: email) do
    it { should exist }
    its('name') { should cmp name }
    its('email') { should cmp email }
    its('display_name') { should cmp display_name }
  end
end
