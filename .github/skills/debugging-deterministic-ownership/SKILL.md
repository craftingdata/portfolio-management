````skill
---
name: deterministic-ownership-debugging
description: Reusable debugging flow for deployment/configuration conflicts caused by multiple automation paths managing the same resource edge. Use for fast triage of infra failures. Includes an Azure RBAC worked example (RoleAssignmentExists).
---

# Deterministic Ownership Debugging

A general-purpose debugging skill for hard-to-reproduce deployment failures where retries do not converge.

This skill is built on one core rule:

**One resource edge should have one owner.**

When two paths (IaC + script/manual) mutate the same edge, retries become non-deterministic and painful.

---

## When This Skill Applies

Use this when you see any of these:

- A deployment fails repeatedly even after “fixes”
- Error says resource “already exists” but expected resource ID/name does not exist
- Multiple automation paths can touch same object (IaC + script + runbook + manual)
- Re-run behavior is inconsistent (sometimes passes, sometimes fails)

---

## 7-Step Debugging Flow

### 1) Start from the system-of-record failure event

- Use deployment operation logs first, not assumptions.
- Isolate **one failed operation ID** and its target scope.

### 2) Build the identity tuple for the failing edge

For any permission/config edge, identify immutable intent fields.

- For RBAC: `(scope, principalId, roleDefinitionId)`
- For other domains, define equivalent tuple (e.g., DNS: zone+record+type)

### 3) Separate declaration vs mutation paths

- Declaration path: IaC (Bicep/Terraform/ARM)
- Mutation paths: scripts/runbooks/manual/API calls

List every place that can create/update/delete that edge.

### 4) Determine ownership and expected identifier strategy

- If IaC owns it, identifier should be deterministic.
- Scripts should only verify, warn, or clean stale state.
- Scripts should not create IaC-owned edges.

### 5) Reconcile drift by tuple (not by generated IDs)

- Query current state by tuple fields.
- Remove stale or non-deterministic duplicates created outside owner path.

### 6) Add preflight guardrails

Before deploy, run a check that fails fast when ownership is violated:

- “Edge exists but identifier does not match owner strategy”
- “Edge created by non-owner path”

### 7) Re-run and verify only the previously failing unit

- Re-run deployment
- Confirm failed operation now succeeds
- Keep broader validation short and targeted

---

## RBAC Worked Example (Azure)

### Symptom

Deployment operation list showed three role assignment creates:

- `7927d0ec-6608-52f6-88ee-9ae73bc08a81` (Succeeded)
- `9de045ee-021d-527c-8842-7d3ce5918fc7` (Succeeded)
- `30520c80-f062-5ca5-bbe6-02dd4c06bdba` (Failed: `RoleAssignmentExists`)

### Root Cause Pattern

- IaC declared deterministic role assignment(s) for Key Vault / ACR.
- Script path had also created Key Vault role assignment(s) imperatively.
- Azure enforces uniqueness by RBAC tuple, so create conflicted even though GUID differed.

### Fix Pattern

- Keep RBAC edge ownership in IaC.
- Remove imperative role-assignment creation for IaC-owned edges.
- Add cleanup step for stale non-deterministic assignments before deployment.

---

## Minimal Command Toolkit (RBAC)

```powershell
# 1) Find failed role-assignment operations in latest deployment
az deployment operation group list -g <rg> -n <deployment> `
  --query "[?properties.targetResource.resourceType=='Microsoft.Authorization/roleAssignments' && properties.provisioningState=='Failed'].{id:properties.targetResource.id,code:properties.statusMessage.error.code}" -o table

# 2) List assignments at failing scope
az role assignment list --scope <scope> -o table

# 3) List assignments for principal across scopes
az role assignment list --all --assignee-object-id <principalObjectId> -o table

# 4) Delete stale conflicting assignment by full ID (if outside owner strategy)
az role assignment delete --ids <roleAssignmentResourceId>
```

---

## Guardrail Checklist (Copy/Paste into PR)

- [ ] Failing operation identified from deployment operations (not inferred)
- [ ] Resource edge tuple documented
- [ ] Single owner declared for that edge
- [ ] Non-owner mutation paths removed or read-only
- [ ] Preflight check added for ownership violations
- [ ] Re-run confirms previously failing op now succeeds

---

## What Generalizes Beyond RBAC

This is not only an RBAC issue.

The same pattern applies to:

- DNS records managed by IaC and scripts
- Secret values/metadata managed by deploy + runbook
- Network ACL/firewall rules managed by two tools
- App settings managed by ARM and app startup scripts

General rule:

**If two paths write the same edge, debugging gets expensive. Design for deterministic ownership first.**

````
