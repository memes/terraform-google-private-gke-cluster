# frozen_string_literal: true

require 'base64'
require 'json'
require 'tempfile'

control 'api' do
  title 'Ensure proxied API access to private GKE cluster succeeds'
  impact 1.0
  proxy_url = input('input_proxy_url')
  endpoint_url = input('output_endpoint_url')
  public_endpoint_url = input('output_public_endpoint_url')
  endpoint_url = public_endpoint_url unless public_endpoint_url.nil? || public_endpoint_url.empty?

  ca_cert = Tempfile.new
  ca_cert.write(Base64.decode64(input('output_ca_cert')))
  ca_cert.close(false)

  gke_auth_cmd = command('gke-gcloud-auth-plugin')
  describe gke_auth_cmd do
    it { should exist }
    its('exit_status') { should eq 0 }
  end
  auth_token = JSON.parse(gke_auth_cmd.stdout)['status']['token']
  describe httprb("#{endpoint_url}/version", auth: { token: auth_token },
                                             ssl: { ca_file: ca_cert.path },
                                             proxy: proxy_url) do
    its('status') { should eq 200 }
    its('body') { should match(/"gitVersion": "v1\.[12][0-9]\.[1-9][0-9]+-gke\.[1-9][0-9]+"/) }
  end
end
