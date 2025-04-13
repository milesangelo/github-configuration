import base64
import logging
import nacl.encoding
import nacl.public

logger = logging.getLogger("github-configurator")

class SecretManager:
    def __init__(self, api_client):
        self.api = api_client

    def create_or_update_secret(self, repo, secret):
        try:
            secret_name = secret["name"]
            secret_value = secret["value"]

            # Step 1: Get the public key for the repo
            url = f"/repos/{repo}/actions/secrets/public-key"
            response = self.api.get(url)
            public_key = response["key"]
            key_id = response["key_id"]

            # Step 2: Encrypt the secret using libsodium (NaCl)
            sealed_box = nacl.public.SealedBox(
                nacl.public.PublicKey(public_key.encode("utf-8"), encoder=nacl.encoding.Base64Encoder)
            )
            encrypted_value = base64.b64encode(sealed_box.encrypt(secret_value.encode("utf-8"))).decode("utf-8")

            # Step 3: Send encrypted value to GitHub
            put_url = f"/repos/{repo}/actions/secrets/{secret_name}"
            payload = {
                "encrypted_value": encrypted_value,
                "key_id": key_id
            }
            self.api.put(put_url, data=payload)

            logger.info(f"✅ Secret '{secret_name}' configured for {repo}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to configure secret '{secret.get('name')}' for {repo}: {str(e)}")
            return False