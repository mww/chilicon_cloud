# Load platform example

This is an example of an integration loading its platforms from its own set up, and passing information on to the platforms.

Use this approach only if your integration is configured solely via `configuration.yaml` and does not use config entries.

### Installation

Copy this folder to `<config_dir>/custom_components/chilicon_cloud/`.

Add the following entry in your `configuration.yaml`:

```yaml
chilicon_cloud:
  username: ${chilicon_username}
  password: !secret chilicon_password
  installation_hash: abcd...123
```
