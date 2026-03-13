# Render Plan

## Job summary
- Job ID: {{ job_id }}
- Prompt: {{ prompt }}
- Location: {{ location }}
- Mode: {{ mode }}
- Imagery source: {{ imagery_source }}
- Video backend: {{ video_backend }}

## Route plan
- Route ID: {{ route_id }}
- Sampling interval: {{ sampling_meters }} m
- Number of sampled viewpoints: {{ sampled_viewpoints }}

## Conditioning assets
- Keyframes directory: {{ keyframes_dir }}
- Depth directory: {{ depth_dir }}
- Camera path file: {{ camera_path_file }}

## Backend execution
- Backend adapter: {{ backend_adapter }}
- Input bundle: {{ conditioning_bundle }}
- Output video: {{ output_video }}

## Evaluation checklist
- Geometry consistency: {{ geometry_consistency }}
- Temporal stability: {{ temporal_stability }}
- Prompt fidelity: {{ prompt_fidelity }}
- Reproducibility: {{ reproducibility }}

## Assumptions
- ASSUMPTION: {{ assumption_1 }}
- ASSUMPTION: {{ assumption_2 }}

## Next actions
1. Validate route coverage.
2. Confirm imagery availability.
3. Generate depth maps.
4. Render the first short segment.
5. Compare against at least one alternate backend.
