locals {
  # Iterate through each master_domain_list resource and extract its ID
  master_adblock_domain_lists = [for k, v in cloudflare_teams_list.master_domain_lists : v.id]

  # Format the values: remove dashes and prepend $
  master_domain_lists_adblock_formatted = [for v in local.master_adblock_domain_lists : format("$%s", replace(v, "-", ""))]

  # Create filters to use in the policy
  master_ad_filters = formatlist("any(dns.domains[*] in %s)", local.master_domain_lists_adblock_formatted)
  master_ad_filter  = join(" or ", local.master_ad_filters)
}

resource "cloudflare_teams_rule" "block_ads" {
  account_id = local.cloudflare_account_id

  name        = "DNS Block Protection"
  description = "DNS Block Protection"

  enabled    = true
  precedence = 11

  # Block domain belonging to lists (defined below)
  filters = ["dns"]
  action  = "block"
  traffic = local.master_ad_filter

  rule_settings {
    block_page_enabled = false
  }

}
