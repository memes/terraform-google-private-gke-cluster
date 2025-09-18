# frozen_string_literal: true

require 'tempfile'

control 'kubeconfig' do
  title 'Verify generated Kubeconfig via kubectl'
  impact 0.7

  kubeconfig = Tempfile.new
  kubeconfig.write(input('output_kubeconfig'))
  kubeconfig.close(false)

  describe command("kubectl --kubeconfig #{kubeconfig.path} version") do
    its('exit_status') { should eq 0 }
    its('stdout') { should match(/Server Version:.*v1\.[123][0-9]\.[0-9]+-gke\.[0-9]+/m) }
  end
end
