# Chilicon Cloud Integration

This integration creates a sensor that exposes solar power data from [Chilicon](https://chiliconpower.com/) microinverters.

This is an integration that loads its platforms from its own set up, based on [this](https://github.com/home-assistant/example-custom-config/tree/master/custom_components/example_load_platform/) example. It also draws heavily from [this](https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_1/) blog post by Aaron Godfrey. It does not use the config flow which is the preferred method to setup integrations.

### Installation

Copy this folder to `<config_dir>/custom_components/chilicon_cloud/`.

Add the following entry in your `configuration.yaml`:

```yaml
chilicon_cloud:
  username: me@example.com
  password: !secret chilicon_password
  installation_hash: abcd...123
```
