package installer

type Variables struct {
	AppDir                   string
	CommonDir                string
	DataDir                  string
	DbPsqlPort               int
	DatabaseDir              string
	ConfigDir                string
	Domain                   string
	SignalingSessionHashkey  string
	SignalingSessionBlockkey string
	SignalingInternalSecret  string
	SignalingBackendSecret   string
	PsqlSharedBuffersMB      int64
	PsqlEffectiveCacheMB     int64
}
