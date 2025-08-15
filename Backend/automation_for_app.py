import geopandas as gpd
import sys
import os
import pandas as pd

__all__ = ['check_osc_duplicates', 'check_invalid_cable_refs', 'report_splice_counts_by_closure', 'process_shapefiles', 'check_gistool_id', 
           'check_cluster_overlaps', 'check_granularity_fields', 'validate_non_virtual_closures', 'validate_feeder_primdistribution_locations','validate_cable_diameters']



###############################################################################################################


def check_osc_duplicates(workspace):
    """
    Checks for duplicated ID values in OUT_Closures.shp (which represent OSCs)
    
    Args:
        workspace (str): Path to the directory containing shapefiles
    
    Returns:
        tuple: (has_issues, json_data) where:
            has_issues: True if duplicates found, False if no duplicates, None if errors
            json_data: Structured validation results
    """
    result = {
        "check_name": "OSC Duplicates Check",
        "status": None,  # Will be "error", "passed", or "failed"
        "summary": {},
        "details": [],
        "errors": []
    }
    
    try:
        shapefile_path = os.path.join(workspace, "OUT_Closures.shp")
        
        if not os.path.isfile(shapefile_path):
            result["status"] = "error"
            result["errors"].append({
                "type": "file_not_found",
                "message": "OUT_Closures.shp not found",
                "path": shapefile_path
            })
            return None, result

        gdf = gpd.read_file(shapefile_path)
        
        # Check for required column
        if 'ID' not in gdf.columns:
            result["status"] = "error"
            result["errors"].append({
                "type": "missing_column",
                "message": "'ID' column not found in OUT_Closures.shp"
            })
            return None, result

        # Check for duplicate IDs
        duplicates = gdf['ID'].duplicated(keep=False)
        
        if duplicates.any():
            result["status"] = "failed"
            result["summary"] = {
                "total_duplicates": int(duplicates.sum()),
                "has_issues": True
            }
            
            # Get duplicate values and their counts
            duplicates_df = gdf[duplicates]['ID'].value_counts().reset_index()
            duplicates_df.columns = ['OSC ID', 'Duplicate Count']
            
            # Add detailed information about duplicates
            for _, row in duplicates_df.iterrows():
                result["details"].append({
                    "osc_id": str(row['OSC ID']),
                    "duplicate_count": int(row['Duplicate Count'])
                })
            
            # Add sample of problematic closures
            problem_closures = gdf[duplicates].head(5)
            result["summary"]["sample_closures"] = problem_closures[['ID', 'IDENTIFIER']].to_dict('records')
            
            return True, result
        else:
            result["status"] = "passed"
            result["summary"] = {
                "message": "No duplicated OSC IDs found",
                "has_issues": False
            }
            return False, result
            
    except Exception as e:
        result["status"] = "error"
        result["errors"].append({
            "type": "processing_error",
            "message": str(e)
        })
        return None, result
    
    
 ##############################################################################################################   

def process_shapefiles(workspace):
    """
    Checks feeder cables and closures without modifying files.
    Reports missing IDENTIFIERs in feeder cables and issues in non-virtual closures.
    Returns: (has_issues: bool, message: str)
    """
    import os
    import geopandas as gpd

    output = ["Processing shapefiles: feeder cables and closures"]
    issues_found = False
    try:
        # Check FeederCables identifier issues without modifying
        feeder_path = os.path.join(workspace, "OUT_FeederCables.shp")
        if not os.path.exists(feeder_path):
            output.append(f"Error: OUT_FeederCables.shp not found in {workspace}")
            return None, "\n".join(output)

        feeder_gdf = gpd.read_file(feeder_path)
        if 'IDENTIFIER' not in feeder_gdf.columns:
            output.append("Feeder cables: 'IDENTIFIER' column missing entirely")
            issues_found = True
        else:
            mask = feeder_gdf['IDENTIFIER'].isna() | (feeder_gdf['IDENTIFIER'] == '')
            if mask.any():
                count = int(mask.sum())
                output.append(
                    f"Feeder cables: {count} record"
                    f"{'s' if count != 1 else ''} have empty IDENTIFIER and require attention"
                )
                issues_found = True
            else:
                output.append("Feeder cables: All IDENTIFIER values are populated")

        output.append("-" * 60)

        # Process Closures
        closures_path = os.path.join(workspace, "OUT_Closures.shp")
        if not os.path.exists(closures_path):
            output.append(f"Error: OUT_Closures.shp not found in {workspace}")
            return None, "\n".join(output)

        closures_gdf = gpd.read_file(closures_path)

        # Check required columns
        missing_cols = [col for col in ('IDENTIFIER', 'VIRTUAL') if col not in closures_gdf.columns]
        if missing_cols:
            output.append(f"Error: Missing columns in closures: {', '.join(missing_cols)}")
            return None, "\n".join(output)

        # Identify problematic closures
        mask = (
            (closures_gdf['VIRTUAL'] == 0) &
            (closures_gdf['IDENTIFIER'].isna() | (closures_gdf['IDENTIFIER'] == ''))
        )
        problem_closures = closures_gdf[mask]
        if not problem_closures.empty:
            count = len(problem_closures)
            output.append(f"⚠️ Problem found in closures: {count} non-virtual closures with empty IDENTIFIER")
            issues_found = True
        else:
            output.append("All non-virtual closures have valid IDENTIFIER values")

        return issues_found, "\n".join(output)

    except Exception as e:
        output.append(f"Unexpected error: {e}")
        return None, "\n".join(output)



###########################################################################################################

def check_gistool_id(workspace):
    output = []
    try:
        seg_path = os.path.join(workspace, "OUT_UsedSegments.shp")
        if not os.path.isfile(seg_path):
            output.append(f"Error: OUT_UsedSegments.shp not found in {workspace}")
            return None, "\n".join(output)
        
        seg_gdf = gpd.read_file(seg_path)
        
        required_cols = ['TYPE', 'GISTOOL_ID', 'ID']
        missing_cols = [col for col in required_cols if col not in seg_gdf.columns]
        if missing_cols:
            output.append(f"Error: Missing required columns: {', '.join(missing_cols)}")
            return None, "\n".join(output)
        
        aerial_buried_mask = seg_gdf['TYPE'].isin(['AERIAL', 'BURIED'])
        non_empty_mask = ~seg_gdf['GISTOOL_ID'].isna() & (seg_gdf['GISTOOL_ID'] != '')
        
        problem_mask = aerial_buried_mask & non_empty_mask
        problem_segments = seg_gdf[problem_mask]
        
        if not problem_segments.empty:
            output.append("\nIssues found in UsedSegments:")
            output.append(f"Found {len(problem_segments)} aerial/buried segments with non-empty GISTOOL_ID")
            output.append("GISTOOL_ID should be empty for aerial/buried segments:")
            output.append("Showing first 5 problematic segments:\n")
            
            report = problem_segments[['TYPE', 'GISTOOL_ID', 'ID']].copy().head(5)
            report['GISTOOL_ID'] = report['GISTOOL_ID'].apply(lambda x: f"'{x}'" if pd.notna(x) else '')
            output.append(report[['TYPE', 'GISTOOL_ID', 'ID']].to_string(index=False))
            
            return True, "\n".join(output)
        else:
            output.append("\nAll aerial and buried segments have empty GISTOOL_ID values")
            return False, "\n".join(output)
            
    except Exception as e:
        output.append(f"Unexpected error: {e}")
        return None, "\n".join(output)
    


############################################################################################################
def check_invalid_cable_refs(workspace):
    """
    Checks all cable piece shapefiles for invalid CableID references
    Returns: (has_issues, message) tuple
    """
    output = []
    has_issues = False
    
    try:
        cable_types = ["Feeder", "Drop", "PrimDistribution", "Distribution"]
        output.append("Checking CableID references for all cable types")

        for layer in cable_types:
            cable_file = f"OUT_{layer}Cables.shp"
            piece_file = f"OUT_{layer}CablePieces.shp"
            cable_path = os.path.join(workspace, cable_file)
            piece_path = os.path.join(workspace, piece_file)

            if not os.path.exists(cable_path):
                output.append(f"Cable file missing: {cable_file}")
                continue
            if not os.path.exists(piece_path):
                output.append(f"Cable piece file missing: {piece_file}")
                continue

            cables = gpd.read_file(cable_path)
            pieces = gpd.read_file(piece_path)

            # Check for invalid CableID references
            valid_ids = set(cables["CABLE_ID"])
            invalid_pieces = pieces[~pieces["CABLE_ID"].isin(valid_ids)]

            if invalid_pieces.empty:
                output.append(f"{layer}CablePieces: All CABLE_IDs are valid.")
            else:
                has_issues = True
                invalid_count = len(invalid_pieces)
                invalid_ids = invalid_pieces["CABLE_ID"].unique()
                output.append(f"{layer}CablePieces: Found {invalid_count} pieces with {len(invalid_ids)} invalid CableIDs")
                output.append("Invalid CableIDs: " + ", ".join(map(str, invalid_ids[:10])))
                if len(invalid_ids) > 10:
                    output.append(f"Showing first 10 of {len(invalid_ids)} invalid IDs")
            output.append("-" * 60)
        
        return has_issues, "\n".join(output)
        
    except Exception as e:
        output.append(f"Unexpected error: {str(e)}")
        return None, "\n".join(output)
    


#############################################################################################################

def report_splice_counts_by_closure(workspace):
    """
    Reports the number of splices per closure and checks against maximum limits
    Returns: tuple (has_issues, message)
    """
    output = []
    has_issues = False
    
    # Define maximum splice limits for each closure type
    MAX_SPLICE_LIMITS = {
        "BE16": 840,
        "flat_dis": 288,
        "OFDC": 96,
        "Budi-S 9-48 HP": 48,
        "POC_UG_1-8HP": 8,
        "Budi-S 49-72 HP": 72
    }
    
    try:
        closure_file = os.path.join(workspace, "OUT_Closures.shp")
        splice_file = os.path.join(workspace, "OUT_Splices.shp")
        output.append("🔍 Reporting splices per closure type")
        
        if not os.path.exists(closure_file):
            output.append("Error: OUT_Closures.shp not found")
            return None, "\n".join(output)
        if not os.path.exists(splice_file):
            output.append("Error: OUT_Splices.shp not found")
            return None, "\n".join(output)
        
        closures = gpd.read_file(closure_file)
        splices = gpd.read_file(splice_file)
        
        # Count splices per closure ID
        splice_counts = splices["ID"].value_counts().reset_index()
        splice_counts.columns = ["ID", "SpliceCount"]
        
        # Merge counts into closures
        closures["ID"] = closures["ID"].astype(str)
        splice_counts["ID"] = splice_counts["ID"].astype(str)
        
        report_df = closures[["IDENTIFIER", "ID"]].copy()
        report_df = report_df.merge(splice_counts, on="ID", how="left")
        report_df["SpliceCount"] = report_df["SpliceCount"].fillna(0).astype(int)
        
        # Find closures that exceed their maximum splice count
        problematic_closures = []
        
        for _, row in report_df.iterrows():
            identifier = row['IDENTIFIER'] if pd.notnull(row['IDENTIFIER']) else 'N/A'
            closure_id = str(row['ID']) if pd.notnull(row['ID']) else 'N/A'
            splice_count = row['SpliceCount']
            
            # Check if this closure type has a defined limit
            if identifier in MAX_SPLICE_LIMITS:
                max_limit = MAX_SPLICE_LIMITS[identifier]
                if splice_count > max_limit:
                    problematic_closures.append({
                        'identifier': identifier,
                        'closure_id': closure_id,
                        'splice_count': splice_count,
                        'max_limit': max_limit
                    })
        
        # Report results - MAINTAIN ORIGINAL OUTPUT FORMAT
        if problematic_closures:
            has_issues = True
            output.append(f"{'Closure Type':<30} {'Closure ID':<20} {'# Splices':<10} {'Message'}")
            output.append("-" * 100)
            
            for closure in problematic_closures:
                message = f"This closure exceeds the maximum number of splices which is {closure['max_limit']}"
                output.append(f"{closure['identifier']:<30} {closure['closure_id']:<20} {closure['splice_count']:<10} {message}")
            
            output.append(f"\nFound {len(problematic_closures)} closure(s) exceeding splice limits.")
        else:
            output.append("All closures are within their maximum splice limits.")
        
        return has_issues, "\n".join(output)
        
    except Exception as e:
        output.append(f"Unexpected error: {str(e)}")
        return None, "\n".join(output)


#################################################################################################

def check_cluster_overlaps(workspace, cluster_files=None):
    """
    Detects overlapping features within each cluster layer shapefile.
    Returns: (has_issues: bool, message: str)
    """
    import geopandas as gpd
    import os

    output = ["🔍 Running cluster self-overlap checks...\n"]
    try:
        if cluster_files is None:
            cluster_files = [
                "OUT_DropClusters.shp",
                "OUT_DistributionClusters.shp",
                "OUT_DistributionCableClusters.shp",
                "OUT_PrimDistributionClusters.shp",
                "OUT_PrimDistributionCableClusters.shp",
                "OUT_FeederClusters.shp",
                "OUT_FeederCableClusters.shp"
            ]

        issues_found = False
        for file in cluster_files:
            path = os.path.join(workspace, file)
            if not os.path.isfile(path):
                output.append(f"⚠️ File not found: {file}")
                continue

            gdf = gpd.read_file(path)
            gdf = gdf[gdf.geometry.notnull()].reset_index(drop=True)

            overlaps = []
            # spatial index for performance
            sindex = gdf.sindex
            for idx, geom in gdf.geometry.items():
                candidates = sindex.query(geom, predicate="intersects")
                for j in candidates:
                    if idx < j and geom.intersects(gdf.geometry[j]):
                        overlaps.append((idx, j))

            if overlaps:
                issues_found = True
                output.append(f"{file}: {len(overlaps)} overlaps found:")
                for a, b in overlaps[:5]:
                    if "CableClusters" in file:
                        id_a = gdf.loc[a].get("CAB_GROUP", a)
                        id_b = gdf.loc[b].get("CAB_GROUP", b)
                        output.append(f"   • Cluster CAB_GROUP {id_a} overlaps with CAB_GROUP {id_b}")
                    else:
                        id_a = gdf.loc[a].get("AGG_ID", a)
                        id_b = gdf.loc[b].get("AGG_ID", b)
                        output.append(f"   • Cluster AGG_ID {id_a} overlaps with Cluster AGG_ID {id_b}")
            else:
                output.append(f"{file}: No overlaps detected.")

            output.append("-" * 60)

        return issues_found, "\n".join(output)

    except Exception as e:
        output.append(f"Error running cluster overlap checks: {e}")
        return None, "\n".join(output)


#################################################################################################

def check_granularity_fields(workspace):
    """
    Validates that CABLEGRAN and BUNDLEGRAN fields are not set to -1 
    in all OUT_<Layer>Cables.shp files.
    Returns: (has_issues: bool, message: str)
    """
    import geopandas as gpd
    import os

    output = ["Checking CABLEGRAN and BUNDLEGRAN values in cable layers...\n"]
    try:
        cable_layers = ["Feeder", "Drop", "Distribution", "PrimDistribution"]
        issues_found = False

        for layer in cable_layers:
            file_name = f"OUT_{layer}Cables.shp"
            path = os.path.join(workspace, file_name)
            if not os.path.isfile(path):
                output.append(f"Missing: {file_name}")
                continue

            gdf = gpd.read_file(path)
            if 'CABLEGRAN' not in gdf.columns or 'BUNDLEGRAN' not in gdf.columns:
                output.append(f"{file_name} is missing CABLEGRAN or BUNDLEGRAN fields.")
                issues_found = True
                continue

            invalid = gdf[(gdf['CABLEGRAN'] == -1) | (gdf['BUNDLEGRAN'] == -1)]
            if not invalid.empty:
                issues_found = True
                count = len(invalid)
                output.append(f"{file_name}: {count} invalid rows:")
                # show up to 5 rows
                preview = invalid[['CABLE_ID', 'CABLEGRAN', 'BUNDLEGRAN']].head(5)
                output.append(preview.to_string(index=False))
            else:
                output.append(f"{file_name}: All granularity values are valid.")

            output.append("-" * 60)

        return issues_found, "\n".join(output)

    except Exception as e:
        output.append(f"Error checking granularity fields: {e}")
        return None, "\n".join(output)





######################################################################################################

def validate_non_virtual_closures(workspace):
    """
    Validates that PrimDistribution, Distribution, and Drop closures are not virtual.
    
    Args:
        workspace (str): Path to Comsof output directory
        
    Returns:
        tuple: (has_issues, message) where:
            has_issues: True if problems found, False otherwise
            message: Detailed validation results
    """


    output = ["🔍 Validating non-virtual closures..."]
    try:
        closure_path = os.path.join(workspace, "OUT_Closures.shp")
        if not os.path.isfile(closure_path):
            output.append(f"Error: OUT_Closures.shp not found in {workspace}")
            return None, "\n".join(output)

        closures = gpd.read_file(closure_path)

        # Check required columns
        required_cols = ['LAYER', 'VIRTUAL', 'EQ_ID']
        missing = [c for c in required_cols if c not in closures.columns]
        if missing:
            output.append(f"Error: Missing required columns: {', '.join(missing)}")
            return None, "\n".join(output)

        # Find closures of the given types that are marked virtual (VIRTUAL == 1)
        mask = (
            closures['LAYER'].isin(['PrimDistribution', 'Distribution', 'Drop']) &
            (closures['VIRTUAL'] == 1)
        )
        bad = closures[mask]

        if not bad.empty:
            output.append(f"Found {len(bad)} closures incorrectly marked as virtual:")
            output.append("These closure types should never be virtual:")
            output.append("- PrimDistribution")
            output.append("- Distribution")
            output.append("- Drop\n")

            # Report using EQ_ID
            report = bad[['EQ_ID', 'LAYER', 'VIRTUAL']].copy()
            report['VIRTUAL'] = report['VIRTUAL'].astype(int)
            output.append(report.to_string(index=False))
            has_issues = True
        else:
            output.append("All PrimDistribution, Distribution, and Drop closures are non-virtual as expected.")
            has_issues = False

        return has_issues, "\n".join(output)

    except Exception as e:
        output.append(f"Unexpected error: {e}")
        return None, "\n".join(output)

#######################################################################################################


def validate_feeder_primdistribution_locations(workspace, tolerance=0.01):
    """
    Validates critical point locations:
    1. Feeder Point and Primary Distribution Point should be separated
    2. No Distribution Point should lie on top of Primary Distribution Points
    
    Args:
        workspace (str): Path to Comsof output directory
        tolerance (float): Maximum allowed distance between points (in CRS units)
        
    Returns:
        tuple: (has_issues, message) where:
            has_issues: True if issues found, False otherwise
            message: Detailed validation results
    """
    output = []
    has_issues = False
    all_issues = []
    
    try:
        # Paths to all required shapefiles
        feeder_path = os.path.join(workspace, "OUT_FeederPoints.shp")
        prim_path = os.path.join(workspace, "OUT_PrimDistributionPoints.shp")
        dist_path = os.path.join(workspace, "OUT_DistributionPoints.shp")
        
        output.append("\n🔍 Validating critical point locations...")
        
        # ==================================================================
        # 1. Validate Feeder Point vs Primary Distribution Point
        # ==================================================================
        output.append("\n=== Feeder Point vs Primary Distribution Point ===")
        
        # Check if files exist
        if not os.path.exists(feeder_path):
            output.append("Error: OUT_FeederPoints.shp not found")
            all_issues.append("feeder_missing")
        if not os.path.exists(prim_path):
            output.append("Error: OUT_PrimDistributionPoints.shp not found")
            all_issues.append("prim_missing")
        
        if "feeder_missing" not in all_issues and "prim_missing" not in all_issues:
            # Load shapefiles
            feeder_points = gpd.read_file(feeder_path)
            prim_points = gpd.read_file(prim_path)
            
            # Check if files have points
            if len(feeder_points) == 0:
                output.append("Error: OUT_FeederPoints.shp is empty")
                all_issues.append("feeder_empty")
            if len(prim_points) == 0:
                output.append("Error: OUT_PrimDistributionPoints.shp is empty")
                all_issues.append("prim_empty")
            
            if len(feeder_points) > 0 and len(prim_points) > 0:
                # Get the first point from each file
                feeder_geom = feeder_points.geometry.iloc[0]
                prim_geom = prim_points.geometry.iloc[0]
                
                # Calculate distance between points
                distance = feeder_geom.distance(prim_geom)
                
                if distance < tolerance:
                    has_issues = True
                    # Get coordinates for reporting
                    feeder_coords = (feeder_geom.x, feeder_geom.y)
                    prim_coords = (prim_geom.x, prim_geom.y)
                    
                    output.append("\nCRITICAL ISSUE: Feeder and Primary Distribution Points are too close!")
                    output.append(f"Distance between points: {distance:.6f} units (tolerance: {tolerance} units)")
                    output.append(f"Feeder Point location: X={feeder_coords[0]:.6f}, Y={feeder_coords[1]:.6f}")
                    output.append(f"Primary Point location: X={prim_coords[0]:.6f}, Y={prim_coords[1]:.6f}")
                    output.append("\nThese points should not be co-located. Please verify in GIS software.")
                else:
                    output.append("\nValidation passed - points are sufficiently separated")
                    output.append(f"Distance: {distance:.6f} units (required > {tolerance} units)")
        
        # ==================================================================
        # 2. Validate Distribution Points vs Primary Distribution Points
        # ==================================================================
        output.append("\n=== Distribution Points vs Primary Distribution Points ===")
        
        # Check if distribution points file exists
        if not os.path.exists(dist_path):
            output.append("Error: OUT_DistributionPoints.shp not found")
            all_issues.append("dist_missing")
        else:
            dist_points = gpd.read_file(dist_path)
            
            if len(dist_points) == 0:
                output.append("Validation passed - Distribution Points file is empty")
            else:
                # Check if we have prim points to compare against
                if "prim_missing" in all_issues or "prim_empty" in all_issues:
                    output.append("Cannot perform validation - Primary Distribution Points are missing or empty")
                else:
                    # Create spatial index for prim points for efficient searching
                    prim_sindex = prim_points.sindex
                    
                    # Find distribution points too close to any prim point
                    problem_points = []
                    
                    for idx, dist_row in dist_points.iterrows():
                        dist_geom = dist_row.geometry
                        
                        # Find possible matches using spatial index
                        possible_matches_index = list(prim_sindex.intersection(dist_geom.bounds))
                        possible_matches = prim_points.iloc[possible_matches_index]
                        
                        # Check exact distance to each possible match
                        for _, prim_row in possible_matches.iterrows():
                            distance = dist_geom.distance(prim_row.geometry)
                            if distance < tolerance:
                                problem_points.append({
                                    'dist_id': dist_row.get('ID', idx),
                                    'dist_coords': (dist_geom.x, dist_geom.y),
                                    'prim_id': prim_row.get('ID', 'Unknown'),
                                    'distance': distance
                                })
                                break  # Only need one violation per distribution point
                    
                    if problem_points:
                        has_issues = True
                        output.append(f"\nPROBLEM: Found {len(problem_points)} Distribution Points too close to Primary Distribution Points")
                        output.append(f"Maximum allowed distance: {tolerance} units")
                        output.append("\nProblematic Distribution Points (first 5):")
                        
                        # Show first 5 problems
                        for point in problem_points[:5]:
                            output.append(f"  Distribution Point ID: {point['dist_id']}")
                            output.append(f"    Coordinates: X={point['dist_coords'][0]:.6f}, Y={point['dist_coords'][1]:.6f}")
                            output.append(f"    Distance to Primary Point ({point['prim_id']}): {point['distance']:.6f} units")
                            output.append("")
                    else:
                        output.append("\nValidation passed - No Distribution Points too close to Primary Distribution Points")
        
        return has_issues, "\n".join(output)
        
    except Exception as e:
        output.append(f"Unexpected error: {e}")
        return None, "\n".join(output)

#######################################################################################################
def validate_cable_diameters(workspace):
    """
    Validates that DIAMETER column is not empty or zero in cable shapefiles.
    
    Args:
        workspace (str): Path to Comsof output directory
        
    Returns:
        tuple: (has_issues, message) where:
            has_issues: True if problems found, False otherwise
            message: Detailed validation results
    """
    output = []
    has_issues = False
    cable_files = [
        "OUT_DistributionCables.shp",
        "OUT_FeederCables.shp",
        "OUT_PrimDistributionCables.shp"
    ]
    
    try:
        output.append("\nValidating cable diameters...")
        any_errors = False
        
        for file in cable_files:
            file_path = os.path.join(workspace, file)
            file_errors = False
            
            if not os.path.exists(file_path):
                output.append(f"Error: {file} not found in workspace")
                any_errors = True
                continue
                
            gdf = gpd.read_file(file_path)
            
            if 'DIAMETER' not in gdf.columns:
                output.append(f"Error: {file} is missing DIAMETER column")
                any_errors = True
                continue
                
            # Find invalid diameters (missing or zero)
            invalid_mask = gdf['DIAMETER'].isna() | (gdf['DIAMETER'] == 0)
            invalid_cables = gdf[invalid_mask]
            
            if not invalid_cables.empty:
                has_issues = True
                file_errors = True
                any_errors = True
                output.append(f"\nPROBLEM: Found {len(invalid_cables)} cables with invalid diameters in {file}")
                output.append("Cables must have non-zero diameter values")
                
                # Show sample of problematic cables
                sample = invalid_cables[['CABLE_ID', 'DIAMETER']].head(5)
                output.append("\nSample of problematic cables:")
                output.append(sample.to_string(index=False))
            else:
                output.append(f"\n{file}: All cables have valid diameters")
        
        if not any_errors:
            output.append("\nAll cable files have valid diameter values")
            
        return has_issues, "\n".join(output)
        
    except Exception as e:
        output.append(f"Unexpected error: {e}")
        return None, "\n".join(output)
    