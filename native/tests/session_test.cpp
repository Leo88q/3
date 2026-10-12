// Noriwake native session tests, Apache-2.0; see ../zooshi/LICENSE.
#include "noriwake/session.h"
#include <cassert>
#include <climits>
#include <iostream>

int main() {
  using noriwake::Session;
  Session run;
  assert(!run.Advance(1000));
  assert(!run.Settle());
  run.Start(Session::kShortRun);
  assert(run.remaining_seconds() == 90);
  assert(!run.Advance(-100));
  assert(!run.Advance(0));
  assert(!run.Advance(89999));
  assert(run.remaining_seconds() == 1);
  const int paused_time = run.elapsed_ms();
  // No call to Advance outside GameplayState: the clock stays unchanged.
  assert(run.elapsed_ms() == paused_time);
  assert(run.Advance(INT_MAX));
  assert(run.remaining_seconds() == 0);
  assert(!run.Advance(1));
  assert(run.Settle());
  assert(!run.Settle());
  run.Start(Session::kClassic);
  assert(!run.Advance(INT_MAX));
  assert(!run.Advance(INT_MAX));
  assert(run.remaining_seconds() == -1);
  assert(run.state() == Session::kRunning);
  assert(!run.Settle());
  run.Finish();
  assert(run.Settle());

  noriwake::LocalProgress progress(-1, -1, -1);
  assert(progress.best_deliveries == 0 && progress.total_deliveries == 0);
  assert(!progress.Record(nullptr, 4));
  run.Start(Session::kShortRun);
  assert(!progress.Record(&run, 24));
  run.Finish();
  assert(!progress.Record(&run, -1));
  assert(progress.Record(&run, 24));
  assert(!progress.Record(&run, 24));
  assert(progress.completed_runs == 1);
  assert(progress.story_chapter() == 0);
  run.Start(Session::kShortRun); run.Finish();
  assert(progress.Record(&run, 1));
  assert(progress.story_chapter() == 1);
  assert(progress.best_deliveries == 24);
  run.Start(Session::kShortRun); run.Finish();
  assert(progress.Record(&run, 75));
  assert(progress.story_chapter() == 2);
  assert(progress.total_deliveries == 100);
  assert(progress.completed_runs == 3);
  noriwake::LocalProgress maxed(INT_MAX, INT_MAX, INT_MAX);
  run.Start(Session::kShortRun); run.Finish();
  assert(maxed.Record(&run, INT_MAX));
  assert(maxed.total_deliveries == INT_MAX && maxed.completed_runs == INT_MAX);
  assert(noriwake::LocalProgress(100, 1, 1).total_deliveries == 100);
  std::cout << "Native session and local progression: all assertions passed.\n";
}
