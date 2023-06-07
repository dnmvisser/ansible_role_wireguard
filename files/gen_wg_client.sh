#!/usr/bin/env bash
if ! command -v wg >/dev/null 2>&1; then
	echo "There is no 'wg' command available, is wireguard installed?"
	exit 1
fi

private_key=$(wg genkey)
echo "- name: $1
  private_key: $private_key
  wg_public_key: $(echo $private_key | wg pubkey)
  preshared_key: $(wg genpsk)"
