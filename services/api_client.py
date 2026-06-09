import os
import pandas as pd
import core
import config
from typing import Tuple, Optional, Dict, Any

class FiduciaryDataService:
    """Fail-safe data service. Fallbacks cleanly to local core functions if FastAPI is standalone."""
    
    @staticmethod
    def get_prospects(filters: Dict[str, Any]) -> pd.DataFrame:
        """Fetch and filter corporate prospects from the pipeline database."""
        prospects_df, _ = core.load_and_merge_data()
        
        # Apply standard filters via core
        filtered = core.apply_filters(
            prospects_df,
            search_term=filters.get("search", ""),
            min_assets=filters.get("min_assets", 0),
            max_assets=filters.get("max_assets"),
            min_participants=filters.get("min_participants", 0),
            max_participants=filters.get("max_participants"),
            status_filter=filters.get("status", "All"),
            industry_filter=filters.get("industry", "All"),
            provider_filter=filters.get("provider", "All"),
            administrator_filter=filters.get("administrator", "All"),
            origin_zip=filters.get("origin_zip", ""),
            max_distance_miles=filters.get("max_distance_miles"),
            data_quality_filter=filters.get("data_quality", "All")
        )
        
        # Apply Sorting
        sort_by = filters.get("sort_by", "Employer Name")
        if not filtered.empty and sort_by in filtered.columns:
            filtered = filtered.sort_values(
                by=sort_by,
                ascending=filters.get("sort_direction") == "Ascending",
                na_position="last",
                kind="mergesort"
            )
            
        return filtered

    @staticmethod
    def get_discovery(filters: Dict[str, Any]) -> pd.DataFrame:
        """Fetch and filter raw DOL Form 5500 filings in Discovery Mode."""
        _, discovery_df = core.load_and_merge_data()
        
        filtered = core.apply_filters(
            discovery_df,
            search_term=filters.get("search", ""),
            min_assets=filters.get("min_assets", 0),
            max_assets=filters.get("max_assets"),
            min_participants=filters.get("min_participants", 0),
            max_participants=filters.get("max_participants"),
            status_filter="All",
            industry_filter=filters.get("industry", "All"),
            provider_filter=filters.get("provider", "All"),
            administrator_filter=filters.get("administrator", "All"),
            origin_zip=filters.get("origin_zip", ""),
            max_distance_miles=filters.get("max_distance_miles"),
            data_quality_filter=filters.get("data_quality", "All")
        )
        
        # Standardize naming columns
        if not filtered.empty and 'Employer Name' not in filtered.columns and 'Employer Name DOL' in filtered.columns:
            filtered['Employer Name'] = filtered['Employer Name DOL']
            
        # Apply Sorting
        sort_by = filters.get("sort_by", "Employer Name")
        if not filtered.empty and sort_by in filtered.columns:
            filtered = filtered.sort_values(
                by=sort_by,
                ascending=filters.get("sort_direction") == "Ascending",
                na_position="last",
                kind="mergesort"
            )
            
        return filtered

    @staticmethod
    def update_pipeline(ein: str, status: str, notes: str) -> bool:
        """Save prospect outreach notes and CRM status updates."""
        try:
            core.save_update(ein, status, notes)
            return True
        except Exception:
            return False
