package installer

import "testing"

func TestPostgresMemoryMB(t *testing.T) {
	cases := []struct {
		totalMB, sharedBuffers, effectiveCacheSize int64
	}{
		{512, 128, 256},
		{1024, 128, 512},
		{4096, 512, 2048},
		{11840, 1480, 5920},
		{65536, 2048, 32768},
	}
	for _, c := range cases {
		shared, cache := postgresMemoryMB(c.totalMB)
		if shared != c.sharedBuffers || cache != c.effectiveCacheSize {
			t.Fatalf("%dMB: expected %d/%d, got %d/%d", c.totalMB, c.sharedBuffers, c.effectiveCacheSize, shared, cache)
		}
	}
}

func TestTotalMemoryMB(t *testing.T) {
	total, err := totalMemoryMB()
	if err != nil {
		t.Fatal(err)
	}
	if total <= 0 {
		t.Fatalf("expected positive memory, got %d", total)
	}
}
