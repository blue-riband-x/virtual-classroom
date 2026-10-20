package com.example.javabackend.controller;

import com.example.javabackend.dto.ApiResponse;
import com.example.javabackend.entity.User;
import com.example.javabackend.mapper.UserMapper;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {
    private final UserMapper userMapper;

    public UserController(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    @GetMapping("/profile")
    public ApiResponse<User> profile(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return ApiResponse.ok(userMapper.findById(userId));
    }

    @PutMapping("/profile")
    public ApiResponse<?> updateProfile(HttpServletRequest request, @RequestBody User user) {
        Long userId = (Long) request.getAttribute("userId");
        user.setId(userId);
        userMapper.update(user);
        return ApiResponse.ok("更新成功", userMapper.findById(userId));
    }

    @GetMapping("/history")
    public ApiResponse<List<Map<String, Object>>> history(HttpServletRequest request) {
        // TODO: 后续接入真实学习记录表
        List<Map<String, Object>> list = new ArrayList<>();
        return ApiResponse.ok(list);
    }

    @GetMapping("/achievements")
    public ApiResponse<List<Map<String, Object>>> achievements(HttpServletRequest request) {
        // TODO: 后续接入真实成就表
        List<Map<String, Object>> list = new ArrayList<>();
        return ApiResponse.ok(list);
    }

    @PostMapping("/learning-count")
    public ApiResponse<?> incrementLearningCount(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        userMapper.incrementLearningCount(userId);
        User updated = userMapper.findById(userId);
        Map<String, Object> result = new HashMap<>();
        result.put("totalLearningCount", updated.getTotalLearningCount());
        return ApiResponse.ok("学习次数+1", result);
    }

    @PostMapping("/add-xp")
    public ApiResponse<?> addXp(HttpServletRequest request, @RequestBody Map<String, Integer> body) {
        Long userId = (Long) request.getAttribute("userId");
        int amount = body.getOrDefault("amount", 0);
        if (amount <= 0) {
            return ApiResponse.error(400, "经验值必须大于0");
        }
        userMapper.incrementXp(userId, amount);
        User updated = userMapper.findById(userId);

        // 处理升级逻辑：与前端一致，xpToNextLevel 每次升级 ×1.2
        int xp = updated.getXp() != null ? updated.getXp() : 0;
        int level = updated.getLevel() != null ? updated.getLevel() : 1;
        int xpToNextLevel = updated.getXpToNextLevel() != null ? updated.getXpToNextLevel() : 100;

        boolean leveledUp = false;
        while (xp >= xpToNextLevel) {
            xp -= xpToNextLevel;
            level++;
            xpToNextLevel = (int) Math.floor(xpToNextLevel * 1.2);
            leveledUp = true;
        }

        if (leveledUp) {
            updated.setXp(xp);
            updated.setLevel(level);
            updated.setXpToNextLevel(xpToNextLevel);
            userMapper.update(updated);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("xp", xp);
        result.put("level", level);
        result.put("xpToNextLevel", xpToNextLevel);
        result.put("leveledUp", leveledUp);
        return ApiResponse.ok("经验值+" + amount, result);
    }
}
