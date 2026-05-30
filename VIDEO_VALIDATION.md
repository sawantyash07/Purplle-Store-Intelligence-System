# Video Validation Report

Validation date: 2026-05-30  
Input folder: `D:\Purplle Store Intelligence System\CCTV Footage`

## Result

**PASS**

The CCTV folder exists and contains five MP4 files. OpenCV opened every file successfully and returned readable dimensions, FPS, and frame counts.

| File | OpenCV Opened | Resolution | FPS | Frames | Duration Seconds |
| --- | --- | --- | ---: | ---: | ---: |
| `CAM 1.mp4` | PASS | 1920x1080 | 29.9700 | 4193 | 139.906 |
| `CAM 2.mp4` | PASS | 1920x1080 | 29.9700 | 3774 | 125.926 |
| `CAM 3.mp4` | PASS | 1920x1080 | 29.9700 | 4436 | 148.015 |
| `CAM 4.mp4` | PASS | 1920x1080 | 25.0000 | 3647 | 145.880 |
| `CAM 5.mp4` | PASS | 1920x1080 | 25.0000 | 3465 | 138.600 |

## Camera Mapping Audit

Representative frames exposed a configuration defect: the previous inferred layout mapped roles to filenames from a different extraction order and omitted `CAM 4.mp4`. The configuration was corrected after visual inspection:

| File | Verified Role | Configured Camera ID |
| --- | --- | --- |
| `CAM 1.mp4` | Additional retail floor, skincare | `CAM_FLOOR_00` |
| `CAM 2.mp4` | Main floor | `CAM_FLOOR_01` |
| `CAM 3.mp4` | Entrance threshold | `CAM_ENTRY_01` |
| `CAM 4.mp4` | Backroom floor view | `CAM_FLOOR_02` |
| `CAM 5.mp4` | Billing counter | `CAM_BILLING_01` |

The inferred polygons remain editable because the official `store_layout.json` referenced by the problem statement was not included in the available extraction.

