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

func TestBrokenAppFromExtraAppsPath(t *testing.T) {
	out := `An unhandled exception has been thrown:
Error: Call to undefined method OC\Server::getContentSecurityPolicyManager() in ` +
		`/var/snap/nextcloud/1011/extra-apps/radio/lib/AppInfo/Application.php:24`

	if got := brokenApp(out); got != "radio" {
		t.Fatalf("expected radio, got %q", got)
	}
}

func TestBrokenAppFromBundledAppPath(t *testing.T) {
	out := `Exception: Call to undefined method OC\Server::getURLGenerator() in file ` +
		`'/var/snap/nextcloud/1011/extra-apps/quicknotes/lib/AppInfo/Application.php' line 70`

	if got := brokenApp(out); got != "quicknotes" {
		t.Fatalf("expected quicknotes, got %q", got)
	}
}

func TestBrokenAppFromAppinfoPath(t *testing.T) {
	out := `Error in /snap/nextcloud/current/nextcloud/apps/files_rightclick/appinfo/app.php`
	if got := brokenApp(out); got != "files_rightclick" {
		t.Fatalf("expected files_rightclick, got %q", got)
	}
}

func TestNoBrokenAppWhenOutputHasNoAppPath(t *testing.T) {
	if got := brokenApp("Doctrine\\DBAL\\Exception: database is gone"); got != "" {
		t.Fatalf("expected empty, got %q", got)
	}
}
