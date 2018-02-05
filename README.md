# helpful-blueprints

Blueprints that provide some useful modules in Cloudify.

**Keys**

`keys.yaml` creates an SSH key and store it as a secret. Delete the deployment forcibly, without executing uninstall to maintain the security of the key material.

How to use:

1. Upload the blueprint to your tenant.
2. Create a Deployment.
3. Execute Install workflow.
4. Delete the deployment with "force delete". Do not execute uninstall.
5. Delete the blueprint.
