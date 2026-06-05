package com.example.javabackend.entity;

import java.time.LocalDateTime;

public class Outline {
    private Long id;
    private Long userId;
    private String title;
    private String topic;
    private String subject;
    private String level;
    private Integer totalDuration;
    private Integer moduleCount;
    private String modulesData;  // JSON string
    private Boolean aiGenerated;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getTopic() { return topic; }
    public void setTopic(String topic) { this.topic = topic; }
    public String getSubject() { return subject; }
    public void setSubject(String subject) { this.subject = subject; }
    public String getLevel() { return level; }
    public void setLevel(String level) { this.level = level; }
    public Integer getTotalDuration() { return totalDuration; }
    public void setTotalDuration(Integer totalDuration) { this.totalDuration = totalDuration; }
    public Integer getModuleCount() { return moduleCount; }
    public void setModuleCount(Integer moduleCount) { this.moduleCount = moduleCount; }
    public String getModulesData() { return modulesData; }
    public void setModulesData(String modulesData) { this.modulesData = modulesData; }
    public Boolean getAiGenerated() { return aiGenerated; }
    public void setAiGenerated(Boolean aiGenerated) { this.aiGenerated = aiGenerated; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
