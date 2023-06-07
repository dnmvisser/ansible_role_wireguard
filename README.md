# ansible_role_wireguard

Ansible role to install and configure a wireguard server on Debian flavor OSes

# Requirements

The bootstrap the configuration, you will need the `wg` command to generate the
various keys. This command comes with the `wireguard` package. It's easiest to
first install that manually on the target host, and generate the keys/config on
there (this is a one time effort).

The `qrencode` command/package is required on the ansible control node.

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
    # Generate this with:
    # privkey=$(wg genkey); echo -e "wg_private_key: $privkey\nwg_public_key:  $(echo $privkey | wg pubkey)"
    wg_private_key: mKprJfzhHr6qQFWTjJ+DNn4YoeGl72hSbMEu0rtpTEM=
    wg_public_key:  i1tcn4Tw0S8aUur+57YJGQ623+ECVj2r+JYeAFUSwBc=

    wg_clients:
      # generate by running the gen_wg_client.sh script:
      # for user in henk frank rob; do ./gen_wg_client.sh $user; done
      - name: henk
        private_key: 0PkVWoVzebEQk6qVDMYmr5P3ZSgWwlWapht0QhrxtXg=
        wg_public_key: fj5+XU9w455S4NLhSvSYbDJWNE4j5PaWkQO43u7Mlxk=
        preshared_key: GiOfhMycS77weMZZcq4x95rc9cXkpMvpRskA4fDr+9M=
      - name: frank
        private_key: aNS7ZHiPWtL9lHCCeGSvwb1llxl+TeeaJvpXLXGzEF4=
        wg_public_key: YjCe3Vxdsle/Z3igCwLtat3vf/NNub/IaJE432gSNCc=
        preshared_key: t6g+i6NFkuFJnTWUJf3abXsq3ptNc2JcpYquj08U+K4=
      - name: rob
        private_key: aEO9GjsfXDZCU/BapQuwuq4OIvIxZS52Lr0u6itSsm0=
        wg_public_key: /IyJzlqI+WAmaYxeD9K5UIneRflFDJaDD1zFn1LUU2M=
        preshared_key: qBb0oVL2TVOxvNFiaErDctoCRsEhQwJDFfTkfHKoWb4=

    wg_postup: >-
      iptables -A FORWARD -i {{ wg_uplink_iface }} -o %i -j ACCEPT;
      iptables -A FORWARD -i %i -j ACCEPT;
      iptables -t nat -A POSTROUTING -o {{ wg_uplink_iface }} -j MASQUERADE;
      ip6tables -A FORWARD -i %i -j ACCEPT;
      ip6tables -t nat -A POSTROUTING -o {{ wg_uplink_iface }} -j MASQUERADE

    wg_postdown: >-
      iptables -D FORWARD -i {{ wg_uplink_iface }} -o %i -j ACCEPT;
      iptables -D FORWARD -i %i -j ACCEPT;
      iptables -t nat -D POSTROUTING -o {{ wg_uplink_iface }} -j MASQUERADE;
      ip6tables -D FORWARD -i %i -j ACCEPT;
      ip6tables -t nat -D POSTROUTING -o {{ wg_uplink_iface }} -j MASQUERADE
```

Deploying this will create two profiles for each client:

* `all` - tunnel all traffic
* `split` - tunnel only traffic for the local IP prefix of the wireguard server.
  In this scenario you will use the tunnel to reach resources at home. See the
  `wg_client_tunnel_flavors` list on how to configure that.

  During deployment all the profiles will be echoed as QR codes, so that you can
  scan one with your android/iOS device. The client profiles will NOT be stored
  anywhere on the server. If you do need to see them as text, supply the
  `wg_debug_client_config` flag as `true`.