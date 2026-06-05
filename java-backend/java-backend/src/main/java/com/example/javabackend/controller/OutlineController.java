package com.example.javabackend.controller;

import com.example.javabackend.dto.ApiResponse;
import com.example.javabackend.entity.Outline;
import com.example.javabackend.service.OutlineService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/outline")
public class OutlineController {
    private final OutlineService outlineService;

    public OutlineController(OutlineService outlineService) {
        this.outlineService = outlineService;
    }

    @GetMapping("/my")
    public ApiResponse<List<Outline>> list(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return ApiResponse.ok(outlineService.listByUserId(userId));
    }

    @GetMapping("/{id}")
    public ApiResponse<Outline> detail(@PathVariable Long id) {
        return ApiResponse.ok(outlineService.getById(id));
    }

    @PutMapping("/{id}/rename")
    public ApiResponse<?> rename(@PathVariable Long id, @RequestBody Map<String, String> body) {
        outlineService.rename(id, body.get("title"));
        return ApiResponse.ok("重命名成功", null);
    }

    @DeleteMapping("/{id}")
    public ApiResponse<?> delete(@PathVariable Long id, HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        outlineService.delete(id, userId);
        return ApiResponse.ok("已删除", null);
    }
}
