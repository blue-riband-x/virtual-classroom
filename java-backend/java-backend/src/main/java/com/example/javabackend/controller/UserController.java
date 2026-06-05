package com.example.javabackend.controller;

import com.example.javabackend.dto.ApiResponse;
import com.example.javabackend.entity.User;
import com.example.javabackend.mapper.UserMapper;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
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
}
