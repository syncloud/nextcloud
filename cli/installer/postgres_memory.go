package installer

import "syscall"

const (
	minSharedBuffersMB = 128
	maxSharedBuffersMB = 2048
)

func totalMemoryMB() (int64, error) {
	var info syscall.Sysinfo_t
	if err := syscall.Sysinfo(&info); err != nil {
		return 0, err
	}
	return int64(uint64(info.Totalram) * uint64(info.Unit) / 1024 / 1024), nil
}

func postgresMemoryMB(totalMB int64) (sharedBuffers, effectiveCacheSize int64) {
	sharedBuffers = min(max(totalMB/8, minSharedBuffersMB), maxSharedBuffersMB)
	effectiveCacheSize = max(totalMB/2, sharedBuffers)
	return sharedBuffers, effectiveCacheSize
}
