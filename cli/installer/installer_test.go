package installer

import "testing"

func TestFailingAppIsTheOneThatStartedAndNeverFinished(t *testing.T) {
	out := `Turned on maintenance mode
Updating database schema
Updated database
Checking whether the database schema for <calendar> can be updated (this can take a long time depending on the database size)
Updating <calendar> ...
Updated <calendar> to 5.0.1
Checking whether the database schema for <contacts> can be updated (this can take a long time depending on the database size)
Updating <contacts> ...
Doctrine\DBAL\Exception: An exception occurred while executing a query
Maintenance mode is kept active`

	if got := failingApp(out); got != "contacts" {
		t.Fatalf("expected contacts, got %q", got)
	}
}

func TestFailingAppWhenSchemaCheckItselfFails(t *testing.T) {
	out := `Turned on maintenance mode
Checking whether the database schema for <calendar> can be updated (this can take a long time depending on the database size)
Doctrine\DBAL\Exception: not able to migrate
Maintenance mode is kept active`

	if got := failingApp(out); got != "calendar" {
		t.Fatalf("expected calendar, got %q", got)
	}
}

func TestNoFailingAppWhenEveryAppFinished(t *testing.T) {
	out := `Updating <calendar> ...
Updated <calendar> to 5.0.1
Updating <contacts> ...
Updated <contacts> to 6.0.0
Doctrine\DBAL\Exception: core migration failed`

	if got := failingApp(out); got != "" {
		t.Fatalf("expected no app to be blamed, got %q", got)
	}
}

func TestNoFailingAppWhenOutputMentionsNoApps(t *testing.T) {
	if got := failingApp("No upgrade required."); got != "" {
		t.Fatalf("expected empty, got %q", got)
	}
}
