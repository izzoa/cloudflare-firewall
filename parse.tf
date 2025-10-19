locals {
  master_domain_list_adblock = split("\n", local.master_combined_lists)

  master_domain_list_clean = [ for x in local.master_domain_list_adblock : x if (x != "") ]

  master_aggregated_lists_adblock = chunklist(local.master_domain_list_clean, 1000)

  master_list_count_adblock = length(local.master_aggregated_lists_adblock)
}

resource "cloudflare_teams_list" "master_domain_lists" {
  account_id = local.cloudflare_account_id

  for_each = {
    for i in range(0, local.master_list_count_adblock) :
      i => element(local.master_aggregated_lists_adblock, i)
  }

  name  = "master_domain_list_${each.key}"
  type  = "DOMAIN"
  items = each.value
}
