package com.example.javabackend.service;

import com.example.javabackend.entity.Outline;
import com.example.javabackend.mapper.OutlineMapper;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class OutlineService {
    private final OutlineMapper outlineMapper;

    public OutlineService(OutlineMapper outlineMapper) {
        this.outlineMapper = outlineMapper;
    }

    public List<Outline> listByUserId(Long userId) {
        return outlineMapper.findByUserId(userId);
    }

    public Outline getById(Long id) {
        return outlineMapper.findById(id);
    }

    public void rename(Long id, String title) {
        outlineMapper.updateTitle(id, title);
    }

    public void delete(Long id, Long userId) {
        outlineMapper.deleteById(id, userId);
    }
}
