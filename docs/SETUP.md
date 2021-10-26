# Ottr Setup Instructions

```sh
cd $HOME/Desktop
virtualenv ottr-venv
cd ottr-venv
source bin/activate
git clone https://github.com/airbnb/ottr.git
cd ottr
export PYTHONPATH=$HOME/Desktop/ottr-venv/ottr/
```

## Build Infrastructure

_Follow the steps in [`infra/README.md`](../infra/README.md) to build the Ottr Core Platform and API._

## Generate ACME Credentials

_These credentials will be used to associate certificates generated to your organization._

```bash
wget -O -  https://get.acme.sh | sh -s email=[EMAIL] # Update Email Field
cd ~/.acme.sh
./acme.sh --set-default-ca --server letsencrypt --register-account
cd ca/acme-v02.api.letsencrypt.org/directory
```

_After your ACME Account has been registered you should see the following
files within `~/.acme.sh/ca/acme-v02.api.letsencrypt.org/directory`:_

- `account.json`
- `account.key`
- `ca.conf`

_After building the Ottr infrastructure there should be those corresponding
files within AWS Secrets Manager, please move the ACME Account information in
the following manner:_

- `account.json` &rarr; `[PREFIX]/otter/account.json`
- `account.key` &rarr; `[PREFIX]/otter/account.key`
- `ca.conf` &rarr; `[PREFIX]/otter/ca.conf`

## Let's Encrypt Rate Limiting

_By default if you are using a dedicated account, Let's Encrypt will cap the
number of certificates issued to approximately 50 per week. If your organization
will need to have this quantity increased you can reach out directly to the
Internet Security Research Group (ISRG) through this
[document](https://docs.google.com/forms/d/e/1FAIpQLSetFLqcyPrnnrom2Kw802ZjukDVex67dOM2g4O8jEbfWFs3dA/viewform)
to request a rate limit increase._

## Getting Running

- The current platforms that are supported are within [`docs/SUPPORT.md`](SUPPORT.md).
- For Ottr to begin executing X.509 certificate rotations the following
  requirements must be met:

  a. Device information is added to database via `PUT /api/v1/assets` API
  endpoint. The device metadata within the database must also match an available
  route within [`route config`](../otter/router/src/config/route.json) and
  [`API route config`](../api/backend/app/config/route.json).

  - The routes determines which ECS Task Definition is run depending on
    the Platform, OS Version, Device Model, and Certificate Authority indexes
    within the database. If your device information does not match any of the
    existing routes, read [`CONTRIBUTE.md`](CONTRIBUTE.md) to see how you can integrate
    additional platforms.

  - [`API Endpoint`](../infra/api.tf): Use variable `api_domain_name` from the `api`
    module.

  ```py
  import requests
  import json

  username = ''
  password = ''

  url = 'https://[API_ENDPOINT]'
  data = {
     "username": username,
     "password": password
  }
  # Authenticate to API
  response = requests.post(url=url + '/user/v1/authenticate', json=data)
  output = json.loads((response.content).decode('utf-8'))
  token = output.get('token')

  # Add Device to Database
  data = {
     "system_name": "subdomain.example.com",
     "common_name": "subdomain.example.com",
     "certificate_authority": "lets_encrypt",
     "data_center": "DC1",
     "device_model": "PA-XXXX",
     "host_platform": "panos",
     "ip_address": "10.0.0.1",
     "os_version": "9.1.0",
     "subject_alternative_name": [
        "subdomain.example.com"
     ]
  }
  response = requests.put(url=url + '/api/v1/assets', headers={"Authorization": token}, json=data)
  print(response.content)

  # Update Device Information
    data = {
     "system_name": "subdomain.example.com",
     "certificate_authority": "lets_encrypt",
     "data_center": "DC1",
     "device_model": "PA-XXXX",
     "host_platform": "panos",
     "ip_address": "10.0.0.1",
     "os_version": "9.1.1",
     "subject_alternative_name": [
        "subdomain.example.com"
     ]
  }
  response = requests.post(url=url + '/api/v1/assets', headers={"Authorization": token}, json=data)
  print(response.content)

   # Target Device has Self-Signed or Invalid Certificate, Used to Unset Certificate Verification for HTTP Requests on First Run
   system_name = 'subdomain.example.com'
   response = requests.patch(url=url + f'/api/v1/management/certificate-validation/set/{system_name}', headers={"Authorization": token})
   print(response.content)
  ```

  b. Create DNS Record for each Common Name (CN) and Subject Alternative Name
  (SANs) on your host that maps to the subdelegate zone, more information in [`dns/README.md`](../dns/README.md).

  ```sh
      module "dns_example" {
         source                  = "./modules/dns"
         certificate_common_name = "subdomain.example.com"
         alias_domain_name       = "example-acme.com"
      }
  ```

  ```sh
  _acme-challenge.subdomain.example.com
  => _acme-challenge.subdomain.example-acme.com
  ```

After this you're all set and Ottr will be ready to automatically handle
end-to-end X.509 certificate rotations for your devices. If you want to test the
workflow you can do a manual certificate rotation against the
`/api/v1/certificate/rotate` API endpoint. You can view the results from the
`otter-step` AWS Step Function and pull ECS Container and CloudWatch Log details
from there.

If there are any questions or issues during the implementation please create a issue within Github.
