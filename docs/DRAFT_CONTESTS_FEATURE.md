# Draft Contests Feature

## Overview

The Draft Contests feature adds a new type of contest to the Over-Under application alongside the existing yes/no contests. Draft contests allow users to participate in fantasy-style drafts where they select items from a pool and compete based on the performance of their drafted items.

## Core Components

### 1. DraftPool
- **Purpose**: Contains collections of draftable items (e.g., NFL players, stocks, etc.)
- **Key Fields**:
  - `pool_name`: Name of the draft pool
  - `description`: Description of what's being drafted
  - `sport`: Optional sport category (NFL, NBA, etc.)
  - `season`: Optional season identifier
- **Methods**:
  - `get_available_items()`: Get undrafted items
  - `get_items_count()`: Total items in pool
  - `get_available_count()`: Available items count

### 2. DraftItem
- **Purpose**: Individual items that can be drafted
- **Key Fields**:
  - `item_name`: Name of the item (e.g., "Josh Allen")
  - `thumbnail_url`: Optional image URL
  - `item_metadata`: JSON field for flexible data (position, team, etc.)
  - `item_order`: Display order
  - `is_available`: Whether item can still be drafted
- **Methods**:
  - `is_drafted()`: Check if item has been picked
  - `get_drafted_by()`: Get the entry that drafted this item
  - `get_total_score()`: Calculate total score based on scoring rules

### 3. DraftContest
- **Purpose**: Main contest entity for draft competitions
- **Key Fields**:
  - `contest_name`: Name of the draft contest
  - `draft_pool_id`: Reference to the pool being drafted
  - `lock_timestamp`: When entries close
  - `picks_per_user`: Number of picks each user gets
  - `draft_order_type`: How draft order is determined ('random', 'manual', 'league_standings')
  - `is_snake_draft`: Whether to use snake draft order
  - `draft_status`: Current status ('pending', 'active', 'completed')
- **Methods**:
  - `is_locked()`: Check if contest is locked
  - `can_start_draft()`: Check if draft can begin
  - `start_draft()`: Initialize draft order and begin
  - `get_current_drafter()`: Get whose turn it is to pick
  - `advance_pick()`: Move to next pick
  - `get_leaderboard()`: Get contest standings

### 4. DraftEntry
- **Purpose**: User participation in a draft contest
- **Key Fields**:
  - `user_id`: User participating
  - `draft_contest_id`: Contest being participated in
  - `draft_position`: Position in draft order
  - `total_score`: Cached total score
- **Methods**:
  - `can_pick_now()`: Check if it's this user's turn
  - `get_remaining_picks()`: How many picks left
  - `get_total_score()`: Calculate current score

### 5. DraftPick
- **Purpose**: Individual picks made during drafting
- **Key Fields**:
  - `draft_entry_id`: Who made the pick
  - `draft_item_id`: What was picked
  - `pick_number`: Overall pick number (1, 2, 3...)
  - `pick_round`: Round number
  - `picked_at`: Timestamp of pick

### 6. DraftScoringRule
- **Purpose**: Defines how items are scored
- **Key Fields**:
  - `rule_name`: Name of the scoring rule
  - `points_per_unit`: Points awarded per unit of stat
  - `category`: Stat category this rule applies to
- **Example**: "Passing Yards" rule gives 0.04 points per yard

### 7. DraftItemScore
- **Purpose**: Actual performance data for items
- **Key Fields**:
  - `draft_item_id`: Item being scored
  - `score_value`: The actual stat value
  - `score_category`: Category of the stat
  - `scoring_period`: When this occurred (week, season, etc.)

### 8. LeagueDraftContest
- **Purpose**: Links draft contests to leagues
- **Key Fields**:
  - `league_id`: League containing the contest
  - `draft_contest_id`: Draft contest in the league
  - `contest_order`: Order within the league

## League Integration

Draft contests can be added to leagues just like regular yes/no contests:

- **League Methods**:
  - `add_draft_contest(draft_contest)`: Add a draft contest to league
  - `remove_draft_contest(draft_contest)`: Remove from league
  - `get_draft_contests()`: Get all draft contests in league
  - `get_total_contest_count()`: Count of all contests (regular + draft)

- **Combined Leaderboards**: Leagues can contain both regular contests and draft contests, with separate tracking for each type.

## Draft Flow

1. **Setup Phase**:
   - Admin creates DraftPool with DraftItems
   - Admin creates DraftContest linked to the pool
   - Users join the contest (create DraftEntry)

2. **Draft Phase**:
   - Contest locks at `lock_timestamp`
   - Draft order is determined based on `draft_order_type`
   - Draft begins (`draft_status` = 'active')
   - Users take turns making picks
   - Each pick advances to the next user

3. **Scoring Phase**:
   - DraftItemScores are added as real-world events occur
   - User scores are calculated based on their picks and scoring rules
   - Leaderboard updates automatically

## Database Schema

The feature adds 8 new tables:
- `draft_pools`
- `draft_items` 
- `draft_contests`
- `draft_entries`
- `draft_picks`
- `draft_scoring_rules`
- `draft_item_scores`
- `league_draft_contests`

All tables include proper foreign key relationships and constraints to maintain data integrity.

## Example Use Cases

### Fantasy Football
- **DraftPool**: "NFL Players 2024"
- **DraftItems**: Individual NFL players with metadata (position, team)
- **Scoring**: Points for yards, touchdowns, etc.

### Stock Picking
- **DraftPool**: "S&P 500 Stocks"
- **DraftItems**: Individual stocks with metadata (sector, market cap)
- **Scoring**: Points based on stock performance

### Entertainment
- **DraftPool**: "Oscar Nominees 2024"
- **DraftItems**: Movies, actors, directors
- **Scoring**: Points for wins in various categories

## Testing

The feature includes comprehensive test coverage:
- `test_draft_models_simple.py`: Basic model functionality
- All models include proper `__repr__` methods for debugging
- Relationships are properly configured with cascade deletes

## Future Enhancements

Potential future additions:
- Real-time draft interface
- Auto-pick functionality for absent users
- Trade system between users
- Multiple scoring periods (weekly, playoffs, etc.)
- Draft history and analytics
- Mobile-optimized draft interface
