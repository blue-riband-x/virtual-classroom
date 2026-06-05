package com.example.javabackend.controller;

import com.example.javabackend.dto.ApiResponse;
import com.example.javabackend.entity.User;
import com.example.javabackend.mapper.UserMapper;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/leaderboard")
public class LeaderboardController {
    private final UserMapper userMapper;

    public LeaderboardController(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    @GetMapping("/xp")
    public ApiResponse<List<User>> xpRank() {
        return ApiResponse.ok(userMapper.findTopByXp(20));
    }

    @GetMapping("/study-time")
    public ApiResponse<List<User>> studyTimeRank() {
        return ApiResponse.ok(userMapper.findTopByStudyTime(20));
    }
}
