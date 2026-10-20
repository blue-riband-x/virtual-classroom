package com.example.javabackend.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.LocalDateTime;

public class User {
    private Long id;
    private String username;
    private String email;
    @JsonIgnore
    private String passwordHash;
    private String nickname;
    private String avatarUrl;
    private Integer xp;
    private Integer level;
    private Integer streak;
    private Double totalLearningHours;
    private Integer totalLearningCount;
    private Integer xpToNextLevel;
    private Boolean isActive;
    private Boolean isSuperuser;
    private LocalDateTime lastLogin;
    private LocalDateTime lastStreakDate;
    private String avatar3dConfig;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }

    public String getNickname() { return nickname; }
    public void setNickname(String nickname) { this.nickname = nickname; }

    public String getAvatarUrl() { return avatarUrl; }
    public void setAvatarUrl(String avatarUrl) { this.avatarUrl = avatarUrl; }

    public Integer getXp() { return xp; }
    public void setXp(Integer xp) { this.xp = xp; }

    public Integer getLevel() { return level; }
    public void setLevel(Integer level) { this.level = level; }

    public Integer getStreak() { return streak; }
    public void setStreak(Integer streak) { this.streak = streak; }

    public Double getTotalLearningHours() { return totalLearningHours; }
    public void setTotalLearningHours(Double totalLearningHours) { this.totalLearningHours = totalLearningHours; }

    public Integer getTotalLearningCount() { return totalLearningCount; }
    public void setTotalLearningCount(Integer totalLearningCount) { this.totalLearningCount = totalLearningCount; }

    public Integer getXpToNextLevel() { return xpToNextLevel; }
    public void setXpToNextLevel(Integer xpToNextLevel) { this.xpToNextLevel = xpToNextLevel; }

    public Boolean getIsActive() { return isActive; }
    public void setIsActive(Boolean isActive) { this.isActive = isActive; }

    public Boolean getIsSuperuser() { return isSuperuser; }
    public void setIsSuperuser(Boolean isSuperuser) { this.isSuperuser = isSuperuser; }

    public LocalDateTime getLastLogin() { return lastLogin; }
    public void setLastLogin(LocalDateTime lastLogin) { this.lastLogin = lastLogin; }

    public LocalDateTime getLastStreakDate() { return lastStreakDate; }
    public void setLastStreakDate(LocalDateTime lastStreakDate) { this.lastStreakDate = lastStreakDate; }

    public String getAvatar3dConfig() { return avatar3dConfig; }
    public void setAvatar3dConfig(String avatar3dConfig) { this.avatar3dConfig = avatar3dConfig; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
