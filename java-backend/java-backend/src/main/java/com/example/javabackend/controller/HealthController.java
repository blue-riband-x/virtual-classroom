package com.example.javabackend.controller;

import com.example.javabackend.dto.ApiResponse;
import org.springframework.web.bind.annotation.*;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/health")
public class HealthController {

    private final DataSource dataSource;

    public HealthController(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @GetMapping("/db")
    public ApiResponse dbCheck() {
        Map<String, Object> result = new HashMap<>();
        try {
            long start = System.currentTimeMillis();
            Connection conn = dataSource.getConnection();
            long elapsed = System.currentTimeMillis() - start;
            
            result.put("status", "OK");
            result.put("connectionTime", elapsed + "ms");
            result.put("url", conn.getMetaData().getURL());
            result.put("userName", conn.getMetaData().getUserName());
            result.put("driverName", conn.getMetaData().getDriverName());
            result.put("driverVersion", conn.getMetaData().getDriverVersion());
            result.put("databaseProductName", conn.getMetaData().getDatabaseProductName());
            result.put("databaseProductVersion", conn.getMetaData().getDatabaseProductVersion());
            conn.close();
        } catch (SQLException e) {
            result.put("status", "FAIL");
            result.put("error", e.getMessage());
            result.put("errorClass", e.getClass().getName());
            if (e.getCause() != null) {
                result.put("rootCause", e.getCause().getMessage());
                result.put("rootCauseClass", e.getCause().getClass().getName());
                if (e.getCause().getCause() != null) {
                    result.put("deepCause", e.getCause().getCause().getMessage());
                    result.put("deepCauseClass", e.getCause().getCause().getClass().getName());
                }
            }
        }
        return ApiResponse.ok(result);
    }
}
