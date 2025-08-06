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
