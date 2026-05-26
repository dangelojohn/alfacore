#!/usr/bin/env bash
# AlfaCore Cosign keypair setup — fresh AlfaCore-specific keypair per Decision Log §scaffold-Q11
#
# Generates a Cosign keypair for signing AlfaCore module releases. Run once,
# offline if possible, before tagging the first release.
#
# Outputs:
#   - alfacore.cosign.key       (PRIVATE — never commit, gitignored)
#   - alfacore.cosign.pub       (public — safe to commit, distribute, verify against)
#
# After generation, upload the private key + password to Forgejo repo secrets:
#   - ALFACORE_COSIGN_KEY        (paste contents of alfacore.cosign.key)
#   - ALFACORE_COSIGN_PASSWORD   (the password you set during generation)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ────────────────────────────────────────────────────────────────────
# 1. Verify cosign is installed
# ────────────────────────────────────────────────────────────────────
if ! command -v cosign &> /dev/null; then
    echo "ERROR: cosign is not installed."
    echo ""
    echo "Install via:"
    echo "  macOS:  brew install cosign"
    echo "  Linux:  curl -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o cosign && chmod +x cosign"
    echo ""
    exit 1
fi

# ────────────────────────────────────────────────────────────────────
# 2. Check for existing keypair (do not overwrite without confirmation)
# ────────────────────────────────────────────────────────────────────
if [[ -f "alfacore.cosign.key" ]]; then
    echo "WARNING: alfacore.cosign.key already exists."
    read -r -p "Overwrite? This will invalidate previous signatures. [y/N] " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted. Existing keypair preserved."
        exit 0
    fi
    rm -f alfacore.cosign.key alfacore.cosign.pub
fi

# ────────────────────────────────────────────────────────────────────
# 3. Generate fresh AlfaCore-specific keypair
# ────────────────────────────────────────────────────────────────────
echo "Generating fresh AlfaCore Cosign keypair..."
echo "You will be prompted for a password. Choose a strong one and store it in your password manager."
echo ""

# COSIGN_PASSWORD env var can be set to avoid interactive prompt
COSIGN_PASSWORD="${COSIGN_PASSWORD:-}" cosign generate-key-pair --output-key-prefix=alfacore.cosign

# ────────────────────────────────────────────────────────────────────
# 4. Confirm and report next steps
# ────────────────────────────────────────────────────────────────────
echo ""
echo "✓ Keypair generated:"
echo "    alfacore.cosign.key       (PRIVATE — gitignored, never commit)"
echo "    alfacore.cosign.pub       (public — safe to commit)"
echo ""
echo "Next steps:"
echo ""
echo "1. Add the public key to the repository:"
echo "   git add alfacore.cosign.pub"
echo "   git commit -m 'chore: add AlfaCore public Cosign verification key'"
echo ""
echo "2. Upload secrets to Forgejo:"
echo "   - Open Forgejo > Settings > Secrets > Repository"
echo "   - Add secret named ALFACORE_COSIGN_KEY with the contents of alfacore.cosign.key"
echo "   - Add secret named ALFACORE_COSIGN_PASSWORD with the password you set above"
echo ""
echo "3. Test signing locally before pushing to CI:"
echo "   echo 'test' | cosign sign-blob --key alfacore.cosign.key -"
echo ""
echo "4. Verify with the public key:"
echo "   echo 'test' | cosign verify-blob --key alfacore.cosign.pub --signature <signature>"
echo ""
echo "5. Store alfacore.cosign.key offline (1Password, hardware vault, etc.) and delete the working copy:"
echo "   shred -u alfacore.cosign.key   # or equivalent secure deletion"
echo ""
echo "The CI workflow at .github/workflows/sign.yml will use ALFACORE_COSIGN_KEY on tagged releases."
