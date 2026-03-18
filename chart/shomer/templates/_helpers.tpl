{{/*
Expand the name of the chart.
*/}}
{{- define "shomer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "shomer.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "shomer.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "shomer.labels" -}}
helm.sh/chart: {{ include "shomer.chart" . }}
{{ include "shomer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "shomer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "shomer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use.
*/}}
{{- define "shomer.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "shomer.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Credentials volume (K8s Secret mounted as files).
*/}}
{{- define "shomer.credentialsVolume" -}}
- name: credentials
  secret:
    secretName: {{ include "shomer.fullname" . }}-credentials
{{- end }}

{{/*
Credentials volumeMount.
*/}}
{{- define "shomer.credentialsVolumeMount" -}}
- name: credentials
  mountPath: /run/credentials
  readOnly: true
{{- end }}

{{/*
Common env vars for shomer containers (database + redis components).
*/}}
{{- define "shomer.commonEnv" -}}
- name: PYTHONPATH
  value: /app/src
- name: CREDENTIALS_DIRECTORY
  value: /run/credentials
- name: SHOMER_DATABASE_HOST
  value: {{ printf "%s-postgres" (include "shomer.fullname" .) | quote }}
- name: SHOMER_DATABASE_USER
  value: {{ .Values.postgres.auth.username | quote }}
- name: SHOMER_DATABASE_NAME
  value: {{ .Values.postgres.auth.database | quote }}
- name: SHOMER_REDIS_HOST
  value: {{ printf "%s-redis" (include "shomer.fullname" .) | quote }}
{{- range $key, $value := .Values.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}

{{/*
Init container that waits for postgres to be ready.
*/}}
{{- define "shomer.waitForPostgres" -}}
{{- if .Values.postgres.enabled }}
{{- $pgHost := printf "%s-postgres" (include "shomer.fullname" .) }}
- name: wait-for-postgres
  image: busybox:1.36
  command: ["sh", "-c", "until nc -z {{ $pgHost }} 5432; do echo waiting for postgres; sleep 2; done"]
{{- end }}
{{- end }}
