# ansible_role_wireguard

Ansible role to install and configure a wireguard server on Debian flavor OSes

# Requirements

The bootstrap the configuration, you will need the `wg` command to generate the
various keys. This command comes with the `wireguard` package. It's easiest to
just install that manually on the target host, and generate the keys/config on
there - this is a one time effort.

The `qrencode` command/package is required on the ansible control node to
display QR codes, that can be used by clients such as smart phones.

# Example playbooks

### Wireguard server behind an ADSL modem

```yaml
---
- name: Deploy wireguard server
  hosts: raspberry1
  become: true

  tasks:
    - name: Include wireguard role
      include_role:
        name: ansible_role_wireguard
        apply:
          tags:
            - wireguard
      tags: always
  vars:
    wg_hostname: my.adsl.ip.address

    # Generate this with:
    # privkey=$(wg genkey); echo -e "wg_private_key: $privkey\nwg_public_key:  $(echo $privkey | wg pubkey)"
    wg_private_key: mKprJfzhHr6qQFWTjJ+DNn4YoeGl72hSbMEu0rtpTEM=
    wg_public_key:  i1tcn4Tw0S8aUur+57YJGQ623+ECVj2r+JYeAFUSwBc=

    wg_clients:
      # Generate these by running the gen_wg_client.sh script inside
      # the files directory:
      # for user in henk youssef rob; do ./gen_wg_client.sh $user; done
      - name: henk
        private_key: 0PkVWoVzebEQk6qVDMYmr5P3ZSgWwlWapht0QhrxtXg=
        public_key: fj5+XU9w455S4NLhSvSYbDJWNE4j5PaWkQO43u7Mlxk=
        preshared_key: GiOfhMycS77weMZZcq4x95rc9cXkpMvpRskA4fDr+9M=
      - name: youssef
        private_key: aNS7ZHiPWtL9lHCCeGSvwb1llxl+TeeaJvpXLXGzEF4=
        public_key: YjCe3Vxdsle/Z3igCwLtat3vf/NNub/IaJE432gSNCc=
        preshared_key: t6g+i6NFkuFJnTWUJf3abXsq3ptNc2JcpYquj08U+K4=
      - name: rob
        private_key: aEO9GjsfXDZCU/BapQuwuq4OIvIxZS52Lr0u6itSsm0=
        public_key: /IyJzlqI+WAmaYxeD9K5UIneRflFDJaDD1zFn1LUU2M=
        preshared_key: qBb0oVL2TVOxvNFiaErDctoCRsEhQwJDFfTkfHKoWb4=
```

Deploying this will create two profiles for each client:

* `all` - tunnel all traffic
* `split` - tunnel only part of the traffic


By default, the `split` profile will only tunnel traffic for the local IP
prefixes of the wireguard server. This is a practical setting to reach
resources at home. If you want to tunnel more, then override
`wg_split_tunnel_extra_prefixes` with a list of those:

```yaml
wg_split_tunnel_extra_prefixes:
  - 216.73.80.0/20
  - 216.239.32.0/19
  - 216.252.220.0/22
  - 2001:4860::/32
  - 2404:6800::/32
  - 2404:f340::/32
  - 2600:1900::/34
```

Note that this is only for convenience and NOT a security measure. It will
cause the profiles to contain these prefixes. As users are free to edit the
profile, they can choose whatever prefixes they wish to tunnel.

If you set `wg_diplay_profiles` to `qr`, then the client configuration
profiles will be echoed as QR codes, for easy scanning with your Android/iOS
device. The client profiles will NOT be stored anywhere on the server. If you
_do_ need to see them as text, then set `wg_display_profiles` to `text`. NOTE:
the profile display feature only works correctly when the stdout callback is set
to `yaml`, which is not the default. Either add this to your `ansible.cfg`:

```ini
[defaults]
stdout_callback = ansible.builtin.yaml
```

Or supply the corresponding environment variable on the command line:

```shell
ANSIBLE_STDOUT_CALLBACK=yaml ansible-playbook vpn.yml -e wg_diplay_profiles=qr ....
```