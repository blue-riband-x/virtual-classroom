package com.example.javabackend.service;

import com.example.javabackend.config.JwtUtil;
import com.example.javabackend.dto.LoginRequest;
import com.example.javabackend.dto.RegisterRequest;
import com.example.javabackend.entity.User;
import com.example.javabackend.mapper.UserMapper;
import org.springframework.stereotype.Service;
import java.util.HashMap;
import java.util.Map;

@Service
public class AuthService {
    private final UserMapper userMapper;
    private final JwtUtil jwtUtil;

    public AuthService(UserMapper userMapper, JwtUtil jwtUtil) {
        this.userMapper = userMapper;
        this.jwtUtil = jwtUtil;
    }

    public Map<String, Object> login(LoginRequest req) {
        User user = userMapper.findByUsername(req.getUsername());
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        if (!req.getPassword().equals(user.getPasswordHash())) {
            throw new RuntimeException("密码错误");
        }
        userMapper.updateLastLogin(user.getId());

        String token = jwtUtil.generateToken(user.getId(), user.getUsername());
        Map<String, Object> result = new HashMap<>();
        result.put("access_token", token);
        result.put("user_id", user.getId());
        result.put("username", user.getUsername());
        result.put("nickname", user.getNickname());
        return result;
    }

    public Map<String, Object> register(RegisterRequest req) {
        User exist = userMapper.findByUsername(req.getUsername());
        if (exist != null) {
            throw new RuntimeException("用户名已存在");
        }

        User user = new User();
        user.setUsername(req.getUsername());
        user.setPasswordHash(req.getPassword());
        user.setEmail(req.getEmail() != null ? req.getEmail() : req.getUsername() + "@test.com");
        user.setNickname(req.getNickname() != null ? req.getNickname() : req.getUsername());
        userMapper.insert(user);

        String token = jwtUtil.generateToken(user.getId(), user.getUsername());
        Map<String, Object> result = new HashMap<>();
        result.put("access_token", token);
        result.put("user_id", user.getId());
        result.put("username", user.getUsername());
        result.put("nickname", user.getNickname());
        return result;
    }

    public User getCurrentUser(Long userId) {
        return userMapper.findById(userId);
    }
}
