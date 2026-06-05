package com.example.javabackend.controller;

import com.example.javabackend.dto.ApiResponse;
import com.example.javabackend.dto.LoginRequest;
import com.example.javabackend.dto.RegisterRequest;
import com.example.javabackend.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public ApiResponse<Map<String, Object>> login(@RequestBody LoginRequest req) {
        try {
            return ApiResponse.ok(authService.login(req));
        } catch (RuntimeException e) {
            return ApiResponse.error(400, e.getMessage());
        }
    }

    @PostMapping("/register")
    public ApiResponse<Map<String, Object>> register(@RequestBody RegisterRequest req) {
        try {
            return ApiResponse.ok(authService.register(req));
        } catch (RuntimeException e) {
            return ApiResponse.error(400, e.getMessage());
        }
    }

    @GetMapping("/me")
    public ApiResponse<?> me(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return ApiResponse.ok(authService.getCurrentUser(userId));
    }
}
