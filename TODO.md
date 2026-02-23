# Content Crawler Todo List

## Phase 1: Add New Sources
- [x] Get YouTube channel IDs
- [x] Update sources.yaml with new YouTube channels
- [x] Add Fantasy Football Scout to sources

## Phase 2: New Blog Post Logic
- [x] Create category-based blog post generator (one post per category, not per video)
- [ ] Add aggregated news summarizer (Fantasy Football Scout)

## Phase 3: Heartbeat Processing
- [x] Create heartbeat script to process one category per run
- [ ] Add rate limiting between runs
- [ ] Track progress in state file

## Phase 4: Testing
- [ ] Test single category fetch
- [ ] Test aggregated blog post
- [ ] Run full crawl
