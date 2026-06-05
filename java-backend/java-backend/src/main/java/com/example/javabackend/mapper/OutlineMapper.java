package com.example.javabackend.mapper;

import com.example.javabackend.entity.Outline;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface OutlineMapper {
    Outline findById(Long id);
    List<Outline> findByUserId(@Param("userId") Long userId);
    int insert(Outline outline);
    int updateTitle(@Param("id") Long id, @Param("title") String title);
    int deleteById(@Param("id") Long id, @Param("userId") Long userId);
}
